"""Wellmanifest governance guard for prefact.

Enforces the Wellmanifest host contract:
"When the current repository has ./project/new-ticket.sh, follow that repository's
GEMINI.md and AGENTS.md. Allocate tickets only through that script. Never commit on
main or a dirty primary checkout."
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class WellmanifestViolationError(RuntimeError):
    """Raised when an operation would violate the Wellmanifest host contract."""


def find_wellmanifest_root(target_path: Path) -> Optional[Path]:
    """Find the enclosing Wellmanifest repository root, if any.

    Walks up from target_path until finding a project/new-ticket.sh,
    .governance/manifest.json, or .worktrees/ directory within a git repository.
    """
    resolved = target_path.resolve()
    current = resolved if resolved.is_dir() else resolved.parent

    while current != current.parent:
        new_ticket = current / "project" / "new-ticket.sh"
        gov_manifest = current / ".governance" / "manifest.json"
        hub_manifest = current / "governance" / "manifest.hub.json"
        git_dir = current / ".git"

        if (new_ticket.is_file() or gov_manifest.is_file() or hub_manifest.is_file()) and git_dir.exists():
            return current

        # Stop if we leave git repository boundary
        if git_dir.exists() and not (new_ticket.is_file() or gov_manifest.is_file()):
            # Could be a parent containing the repo, keep searching
            pass

        current = current.parent

    return None


def is_wellmanifest_repo(target_path: Path) -> bool:
    """Return True if target_path is governed by Wellmanifest standards."""
    return find_wellmanifest_root(target_path) is not None


def is_safe_to_modify(target_path: Path) -> Tuple[bool, str]:
    """Check if target_path is safe to mutate in-place under Wellmanifest rules.

    Returns:
        (is_safe, rationale_message)
    """
    repo_root = find_wellmanifest_root(target_path)
    if repo_root is None:
        return True, "Target is not inside a Wellmanifest-governed repository."

    resolved_target = target_path.resolve()
    worktrees_dir = (repo_root / ".worktrees").resolve()

    # If the file is inside the .worktrees/ directory, it is in an isolated ticket worktree
    try:
        if worktrees_dir.is_dir() and resolved_target.is_relative_to(worktrees_dir):
            return True, f"Target is located inside an isolated ticket worktree: {worktrees_dir}"
    except (ValueError, AttributeError):
        pass

    # Query current git branch in the repository root
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        current_branch = result.stdout.strip()
    except Exception as e:
        return False, f"Failed to determine git branch: {e}"

    if current_branch in ("main", "master"):
        return False, (
            f"Blocked by Wellmanifest Host Contract: target file '{target_path.name}' is in repository "
            f"'{repo_root.name}' on branch '{current_branch}'. Modifying files directly on 'main' or a primary "
            f"checkout is strictly forbidden. Work must be conducted in an isolated ticket worktree allocated "
            f"via ./project/new-ticket.sh."
        )

    # If branch contains ticket- or ticket/, it is a dedicated ticket branch
    if "ticket-" in current_branch or "ticket/" in current_branch:
        return True, f"Target is on dedicated ticket branch: {current_branch}"

    # Other branch: allow if primary checkout is dedicated
    return True, f"Target is on non-main branch: {current_branch}"
