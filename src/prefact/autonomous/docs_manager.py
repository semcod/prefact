"""Documentation management for autonomous prefact."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

from ._base import BaseManager, console


class DocsManager(BaseManager):
    """Manages documentation files - planfile.yaml and CHANGELOG.md."""

    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.tickets_created: List[Dict[str, Any]] = []
        self.issues_found: List[Dict[str, Any]] = []

    def update_planfile(self) -> None:
        """Update planfile.yaml with new tickets."""
        # Load existing planfile or create new
        if self.planfile_path.exists():
            with open(self.planfile_path) as f:
                planfile = yaml.safe_load(f) or {}
        else:
            planfile = self.create_default_planfile()

        self._remove_obsolete_tickets(planfile)
        new_tickets, skipped_tickets = self._collect_new_tickets(planfile)
        self._insert_new_tickets(planfile, new_tickets)

        # Save planfile
        with open(self.planfile_path, "w") as f:
            yaml.dump(planfile, f, default_flow_style=False, sort_keys=False)

        self.tickets_created = new_tickets
        if skipped_tickets > 0:
            console.print(
                f"🎫 Created {len(new_tickets)} tickets in planfile.yaml ({skipped_tickets} issue groups skipped by limit)",
                style="yellow",
            )
        else:
            console.print(f"🎫 Created {len(new_tickets)} tickets in planfile.yaml")

    def _current_issue_keys(self) -> set[tuple[str, tuple[str, ...]]]:
        current_issue_keys = set()
        for issue_group in self.issues_found:
            rel_file = self._get_relative_file_path(issue_group["file"])
            current_issue_keys.add((issue_group["rule_id"], tuple([rel_file])))
        return current_issue_keys

    def _remove_obsolete_tickets(self, planfile: Dict[str, Any]) -> None:
        """Remove tickets for issues that are no longer present, in place."""
        current_issue_keys = self._current_issue_keys()
        removed_count = 0

        if "backlog" in planfile and isinstance(planfile["backlog"], list):
            patterns = planfile["backlog"]
            planfile["backlog"] = [
                t
                for t in patterns
                if not self._should_remove_obsolete_ticket(t, current_issue_keys)
            ]
            removed_count += len(patterns) - len(planfile["backlog"])

        for sprint in planfile.get("sprints", []):
            for field in ["tasks", "task_patterns"]:
                if field in sprint and isinstance(sprint[field], list):
                    patterns = sprint[field]
                    sprint[field] = [
                        t
                        for t in patterns
                        if not self._should_remove_obsolete_ticket(
                            t, current_issue_keys
                        )
                    ]
                    removed_count += len(patterns) - len(sprint[field])

        if removed_count > 0:
            console.print(
                f"🧹 Removed {removed_count} obsolete tickets from planfile.yaml"
            )

    def _collect_new_tickets(
        self, planfile: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], int]:
        """Build the list of new tickets to add, honoring the ticket limit."""
        new_tickets: List[Dict[str, Any]] = []
        seen_tickets = set()
        max_tickets = self.get_autonomous_limit("autonomous_max_tickets")
        skipped_tickets = 0

        for issue_group in self.issues_found:
            ticket = self.create_ticket_from_issue(issue_group)
            ticket_key = (ticket["rule_id"], tuple(ticket["files"]))

            if ticket_key in seen_tickets or self.ticket_exists(planfile, ticket):
                continue

            if (
                self._count_existing_tickets(planfile) + len(new_tickets)
                >= max_tickets
            ):
                skipped_tickets = len(self.issues_found) - len(new_tickets)
                console.print(
                    f"⚠️ Ticket limit reached ({max_tickets}); skipping {max(0, skipped_tickets)} remaining autonomous tickets.",
                    style="yellow",
                )
                break

            new_tickets.append(ticket)
            seen_tickets.add(ticket_key)

        return new_tickets, skipped_tickets

    def _insert_new_tickets(
        self, planfile: Dict[str, Any], new_tickets: List[Dict[str, Any]]
    ) -> None:
        """Insert new tickets into the planfile's backlog or first sprint, in place."""
        if not new_tickets:
            return

        if "backlog" in planfile:
            if not isinstance(planfile["backlog"], list):
                planfile["backlog"] = []
            planfile["backlog"].extend(new_tickets)
            return

        if "sprints" not in planfile:
            planfile["sprints"] = []

        if not planfile["sprints"]:
            planfile["sprints"].append(
                {
                    "id": "sprint-1",
                    "name": "Code Quality Improvements",
                    "duration": "2 weeks",
                    "objectives": ["Fix code quality issues"],
                    "task_patterns": [],
                }
            )

        sprint = planfile["sprints"][0]
        field = "tasks" if "tasks" in sprint else "task_patterns"
        if field not in sprint:
            sprint[field] = []

        sprint[field].extend(new_tickets)

    def _count_existing_tickets(self, planfile: Dict[str, Any]) -> int:
        total = 0
        for sprint in planfile.get("sprints", []):
            total += len(sprint.get("tasks", []))
            total += len(sprint.get("task_patterns", []))
        return total

    def _should_remove_obsolete_ticket(
        self, ticket: Any, current_issue_keys: set[tuple[str, tuple[str, ...]]]
    ) -> bool:
        if not isinstance(ticket, dict):
            return False
        if not self._is_autonomous_ticket(ticket):
            return False
        rule_id = ticket.get("rule_id")
        files = tuple(ticket.get("files", []))
        return (rule_id, files) not in current_issue_keys

    @staticmethod
    def _is_autonomous_ticket(ticket: dict[str, Any]) -> bool:
        return (
            isinstance(ticket.get("rule_id"), str)
            and isinstance(ticket.get("files"), list)
            and ticket.get("id", "").startswith("ticket-")
            and isinstance(ticket.get("count"), int)
            and isinstance(ticket.get("model_hints"), dict)
        )

    def create_default_planfile(self) -> Dict[str, Any]:
        """Create default planfile structure."""
        return {
            "name": "Code Quality Improvement",
            "project_name": self.project_root.name,
            "project_type": "prefactoring",
            "domain": "dev-tools",
            "goal": "Improve code quality using prefact",
            "goals": [
                "Fix all prefact-detected issues",
                "Improve code maintainability",
                "Ensure consistent code style",
            ],
            "quality_gates": [{"metric": "Prefact Issues", "threshold": "0"}],
            "sprints": [],
        }

    def create_ticket_from_issue(self, issue_group: Dict[str, Any]) -> Dict[str, Any]:
        """Create a ticket from an issue group."""
        # Generate unique ID from issue content
        # Use relative path for consistent hashing across different environments
        file_path = Path(issue_group["file"])
        if file_path.is_absolute():
            try:
                rel_file = str(
                    file_path.resolve().relative_to(self.project_root.resolve())
                )
            except ValueError:
                rel_file = str(file_path)
        else:
            rel_file = str(file_path)

        content_hash = hashlib.md5(
            f"{issue_group['rule_id']}:{rel_file}".encode()
        ).hexdigest()[:8]

        # Determine priority based on severity and count
        priority = "medium"
        if issue_group["severity"] == "error":
            priority = "critical"
        elif issue_group["count"] > 5:
            priority = "high"

        # Estimate based on count
        estimate = (
            "1d"
            if issue_group["count"] <= 3
            else "2d"
            if issue_group["count"] <= 10
            else "3d"
        )

        return {
            "id": f"ticket-{content_hash}",
            "name": f"Fix {issue_group['rule_id']} issues",
            "description": f"Resolve {issue_group['count']} {issue_group['rule_id']} issues in {rel_file}",
            "task_type": "bugfix"
            if issue_group["severity"] == "error"
            else "prefactor",
            "priority": priority,
            "estimate": estimate,
            "files": [rel_file],
            "rule_id": issue_group["rule_id"],
            "count": issue_group["count"],
            "model_hints": {"planning": "balanced", "implementation": "balanced"},
        }

    def ticket_exists(self, planfile: Dict[str, Any], ticket: Dict[str, Any]) -> bool:
        """Check if ticket already exists in planfile."""
        for sprint in planfile.get("sprints", []):
            # Check both 'tasks' and legacy 'task_patterns'
            for field in ["tasks", "task_patterns"]:
                for existing in sprint.get(field, []):
                    if (
                        existing.get("rule_id") == ticket["rule_id"]
                        and existing.get("files") == ticket["files"]
                    ):
                        return True
        return False

    def _detect_project_version(self) -> str:
        """Read the target project's own version from its pyproject.toml.

        Falls back to "Unreleased" (rather than a hardcoded placeholder) when
        the file is missing or has no [project].version — the entry still
        needs a heading, but claiming a specific version number that wasn't
        actually read from the project would be misleading.
        """
        pyproject = self.project_root / "pyproject.toml"
        if not pyproject.exists():
            return "Unreleased"

        try:
            try:
                import tomllib  # Python 3.11+
            except ModuleNotFoundError:
                import tomli as tomllib  # type: ignore[no-redef]

            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            version = data.get("project", {}).get("version")
            return version if isinstance(version, str) and version else "Unreleased"
        except Exception:
            return "Unreleased"

    def update_changelog_md(self) -> None:
        """Update CHANGELOG.md with recent changes."""
        if not self.tickets_created:
            return

        # Create changelog entry
        version = self._detect_project_version()
        date = datetime.now().strftime("%Y-%m-%d")

        entry = f"## [{version}] - {date}\n\n"
        entry += "### Fixed\n"

        for ticket in self.tickets_created:
            entry += f"- {ticket['name']} ({ticket['id']})\n"

        # Write CHANGELOG.md
        if self.changelog_path.exists():
            existing = self.changelog_path.read_text()
            # Insert after first header
            lines = existing.split("\n")
            insert_pos = 1
            while insert_pos < len(lines) and not lines[insert_pos].startswith("##"):
                insert_pos += 1

            new_content = f"{chr(10).join(lines[:insert_pos])}\n{entry}\n{chr(10).join(lines[insert_pos:])}"
        else:
            new_content = f"# Changelog\n\n{entry}"

        self.changelog_path.write_text(new_content)
        console.print(
            f"📝 Updated CHANGELOG.md with {len(self.tickets_created)} changes"
        )

    def _get_relative_file_path(self, file_path: str) -> str:
        """Convert file path to relative path for better portability."""
        path = Path(file_path)
        if path.is_absolute():
            try:
                return str(path.resolve().relative_to(self.project_root.resolve()))
            except ValueError:
                return str(file_path)
        return str(file_path)
