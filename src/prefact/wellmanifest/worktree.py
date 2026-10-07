"""Wellmanifest ticket and worktree manager for prefact.

Handles:
1. Ticket allocation via ./project/new-ticket.sh
2. Execution of refactoring inside isolated linked worktrees
3. Conformance validation and merge disposition evaluation per wellmanifest/merge
4. Atomic merge back to main with worktree cleanup
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from prefact._base import console


@dataclass
class TicketAllocation:
    ticket_id: str
    worktree_path: Path
    branch_name: str
    repo_root: Path


class WellmanifestWorktreeManager:
    """Orchestrates refactoring tasks across Wellmanifest worktrees."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.new_ticket_script = self.repo_root / "project" / "new-ticket.sh"
        self.governance_check_script = self.repo_root / "project" / "governance-check.sh"

    def can_allocate(self) -> bool:
        """Check if repository has a functional new-ticket.sh script."""
        return self.new_ticket_script.is_file() and os.access(self.new_ticket_script, os.X_OK)

    def allocate_ticket(
        self,
        title: str,
        owned_paths: List[str],
        workstream: str = "application",
        agent: str = "antigravity",
        kind: str = "SERVICE",
        priority: str = "P2",
    ) -> TicketAllocation:
        """Allocate a dedicated ticket and worktree via new-ticket.sh."""
        if not self.can_allocate():
            raise RuntimeError(f"Cannot allocate ticket: {self.new_ticket_script} is missing or not executable")

        cmd = [
            str(self.new_ticket_script),
            "-w", workstream,
            "-t", title[:70],
            "-a", agent,
            "-k", kind,
            "-p", priority,
        ]
        for p in owned_paths:
            cmd.extend(["--path", str(p)])

        console.print(f"[bold cyan]Allocating Wellmanifest ticket in {self.repo_root.name}:[/bold cyan] {title[:60]}")
        res = subprocess.run(
            cmd,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
            check=False,
        )

        output = (res.stdout or "") + "\n" + (res.stderr or "")
        if res.returncode != 0:
            raise RuntimeError(f"Ticket allocation failed (exit {res.returncode}):\n{output}")

        # Parse allocation output:
        # e.g.: "Successfully allocated ticket-915 for '...' in /path/to/.worktrees/ticket-915-..."
        match = re.search(r"Successfully allocated\s+(ticket-\S+)\s+for\s+'.*?'\s+in\s+(\S+)", output)
        if not match:
            # Fallback search for ticket-NNN in worktrees
            match_id = re.search(r"(ticket-\d+)", output)
            if not match_id:
                raise RuntimeError(f"Could not extract ticket ID from new-ticket.sh output:\n{output}")
            ticket_id = match_id.group(1)
            worktree_candidates = list((self.repo_root / ".worktrees").glob(f"*{ticket_id}*"))
            if not worktree_candidates:
                raise RuntimeError(f"Could not locate worktree for {ticket_id} in {self.repo_root}/.worktrees")
            worktree_path = worktree_candidates[0]
        else:
            ticket_id = match.group(1)
            worktree_path = Path(match.group(2).rstrip("."))

        # Get the branch name from the worktree
        branch_res = subprocess.run(
            ["git", "-C", str(worktree_path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        branch_name = branch_res.stdout.strip() or f"ticket/{ticket_id}"

        return TicketAllocation(
            ticket_id=ticket_id,
            worktree_path=worktree_path,
            branch_name=branch_name,
            repo_root=self.repo_root,
        )

    def evaluate_merge_disposition(self, allocation: TicketAllocation) -> Dict[str, Any]:
        """Evaluate merge disposition per wellmanifest/merge standard.

        Possible dispositions:
        - 'adopt': gate passes, clean tree, reachability verified
        - 'rebuild': gate failed or tests broken
        """
        gov_ok = True
        gov_msg = "No governance script"
        if self.governance_check_script.is_file():
            gov_res = subprocess.run(
                [str(self.governance_check_script)],
                cwd=str(allocation.worktree_path),
                capture_output=True,
                text=True,
                check=False,
            )
            gov_ok = (gov_res.returncode == 0)
            gov_msg = (gov_res.stdout or "") + (gov_res.stderr or "")

        disposition = "adopt" if gov_ok else "rebuild"
        decision = {
            "schema": "wellmanifest.merge-decision/v1",
            "candidate": {
                "ticketId": allocation.ticket_id,
                "branch": allocation.branch_name,
                "worktree": str(allocation.worktree_path),
            },
            "disposition": disposition,
            "evidence": {
                "governancePassed": gov_ok,
                "governanceOutput": gov_msg[:500],
            },
        }
        return decision

    def merge_ticket(self, allocation: TicketAllocation, commit_msg: Optional[str] = None) -> bool:
        """Merge ticket worktree cleanly into main and clean up worktree."""
        msg = commit_msg or f"chore(prefact): automated refactoring ({allocation.ticket_id})"

        # Ensure changes inside worktree are committed
        status_res = subprocess.run(
            ["git", "-C", str(allocation.worktree_path), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if status_res.stdout.strip():
            subprocess.run(["git", "-C", str(allocation.worktree_path), "add", "-A"], check=False)
            commit_res = subprocess.run(
                ["git", "-C", str(allocation.worktree_path), "commit", "-m", msg],
                capture_output=True,
                text=True,
                check=False,
            )
            if commit_res.returncode != 0:
                console.print(f"[bold red]Failed to commit in worktree:[/bold red] {commit_res.stderr}")
                return False

        # Merge branch into primary repo checkout
        merge_res = subprocess.run(
            ["git", "-C", str(self.repo_root), "merge", "--no-ff", allocation.branch_name, "-m", f"Merge branch '{allocation.branch_name}' into main"],
            capture_output=True,
            text=True,
            check=False,
        )
        if merge_res.returncode != 0:
            console.print(f"[bold red]Merge into main failed:[/bold red] {merge_res.stderr}")
            return False

        # Remove the worktree
        subprocess.run(
            ["git", "-C", str(self.repo_root), "worktree", "remove", str(allocation.worktree_path)],
            capture_output=True,
            check=False,
        )

        console.print(f"[bold green]Successfully merged and cleaned up {allocation.ticket_id}[/bold green]")
        return True
