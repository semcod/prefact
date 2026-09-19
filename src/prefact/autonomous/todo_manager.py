"""TODO management for autonomous prefact.

The manager is the façade wiring together three cohesive submodules:

- :mod:`prefact.autonomous.todo_ownership` — splitting TODO.md into manual
  and prefact-owned regions (including legacy migration);
- :mod:`prefact.autonomous.todo_planning` — deriving todo state from the
  owned block;
- :mod:`prefact.autonomous.todo_render` — rendering the owned block.

Execution (running fixes for pending tasks) stays here because it owns the
scanner/fixer wiring.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

from prefact.config import Config
from prefact.config_extended import ExtendedConfig
from prefact.fixer import Fixer
from prefact.scanner import Scanner

from ._base import BaseManager, console
from .todo_ownership import PREFACT_BEGIN, PREFACT_END, split_existing
from .todo_planning import (
    find_completed_tasks,
    generate_current_todos,
    parse_existing_todos,
    parse_todo_tasks,
)
from .todo_render import build_execution_block, build_todo_block

__all__ = ["PREFACT_BEGIN", "PREFACT_END", "TodoManager"]


class TodoManager(BaseManager):
    """Manages TODO.md file operations."""

    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.issues_found: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Ownership: read/write the prefact-owned block, preserving the rest
    # ------------------------------------------------------------------

    def _split_existing(self) -> Tuple[str, str, str]:
        """Return ``(before, owned, after)`` of the current TODO.md."""
        if not self.todo_path.exists():
            return "", "", ""
        return split_existing(self.todo_path.read_text())

    def _write_owned_block(self, block: str) -> None:
        """Replace prefact's block in TODO.md, preserving manual content."""
        before, _owned, after = self._split_existing()
        parts: List[str] = []
        if before.strip():
            parts.append(before.rstrip() + "\n\n")
        parts.append(f"{PREFACT_BEGIN}\n{block.rstrip()}\n{PREFACT_END}\n")
        if after.strip():
            parts.append("\n" + after.strip() + "\n")
        self.todo_path.write_text("".join(parts))

    def update_todo_md(self) -> None:
        """Update TODO.md with current issues, marking completed tasks."""
        # Parse existing TODO.md if it exists
        existing_todos, _completed_todos = self._parse_existing_todos()

        # Create set of current issues and generate new todos
        current_issues, new_todos, total_active_todos = self._generate_current_todos(
            existing_todos
        )

        # Find completed tasks (exist in TODO.md but not in current issues)
        completed_tasks, total_completed_todos = self._find_completed_tasks(
            existing_todos, current_issues
        )

        # Build and write TODO.md content
        block = build_todo_block(
            new_todos, completed_tasks, total_active_todos, total_completed_todos
        )
        self._write_owned_block(block)

        total_items = total_active_todos + total_completed_todos
        console.print(
            f"📝 Updated TODO.md: {total_active_todos} active, {total_completed_todos} completed ({total_items} total)"
        )

    def _parse_existing_todos(self) -> Tuple[Dict, List]:
        """Parse existing prefact-owned TODO entries."""
        _before, owned, _after = self._split_existing()
        return parse_existing_todos(owned, self._get_relative_file_path)

    def _generate_current_todos(self, existing_todos: Dict) -> Tuple[set, List[str], int]:
        """Generate todos for current issues."""
        max_todo_items = self.get_autonomous_limit("autonomous_max_todo_items")
        return generate_current_todos(
            self.issues_found, existing_todos, max_todo_items,
            self._get_relative_file_path,
        )

    def _find_completed_tasks(
        self, existing_todos: Dict, current_issues: set
    ) -> Tuple[List[str], int]:
        """Find tasks that were completed since last run."""
        max_completed_todos = self.get_autonomous_limit(
            "autonomous_max_completed_todos"
        )
        return find_completed_tasks(existing_todos, current_issues, max_completed_todos)

    def _get_relative_file_path(self, file_path: str) -> str:
        """Convert file path to relative path for better portability."""
        path = Path(file_path)
        if path.is_absolute():
            try:
                return str(path.resolve().relative_to(self.project_root.resolve()))
            except ValueError:
                return str(file_path)
        return str(file_path)

    # ------------------------------------------------------------------
    # Execution of pending TODO tasks
    # ------------------------------------------------------------------

    def execute_todos(self) -> None:
        """Execute all tasks from TODO.md, marking completed ones and removing obsolete ones."""
        if not self.todo_path.exists():
            console.print("❌ TODO.md not found. Run autonomous mode first.")
            return

        console.print("🔧 Executing TODO tasks...")

        # Parse tasks from TODO.md
        active_tasks = self._parse_todo_tasks()

        if not active_tasks:
            console.print("ℹ️ No active tasks found.")
            return

        tasks_to_execute, deferred_tasks = self._limit_todo_execution_tasks(
            active_tasks
        )

        # Execute tasks using the refactoring engine
        executed_count, completed_tasks = self._execute_todo_tasks(tasks_to_execute)
        completed_tasks.extend(task["original_line"] for task in deferred_tasks)

        # Update TODO.md with results
        self._update_todo_with_execution_results(
            completed_tasks,
            executed_count,
            len(tasks_to_execute),
            len(active_tasks),
        )

    def _parse_todo_tasks(self) -> List[Dict[str, Any]]:
        """Parse active tasks from the prefact-owned block of TODO.md."""
        _before, owned, _after = self._split_existing()
        return parse_todo_tasks(owned)

    def _get_refactoring_config(self):
        """Get configuration for the refactoring engine."""
        if self.refact_config_path.exists():
            try:
                config = ExtendedConfig.from_yaml(self.refact_config_path)
            except Exception:
                config = Config.from_yaml(self.refact_config_path)
        else:
            config = Config()
        config.project_root = self.project_root
        return config

    def _limit_todo_execution_tasks(
        self, active_tasks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        max_execution_items = self.get_autonomous_limit(
            "autonomous_max_todo_execution_items"
        )
        tasks_to_execute = active_tasks[:max_execution_items]
        deferred_tasks = active_tasks[max_execution_items:]

        if deferred_tasks:
            console.print(
                f"⚠️ TODO execution limit reached ({max_execution_items}); deferring {len(deferred_tasks)} tasks to the next run.",
                style="yellow",
            )

        return tasks_to_execute, deferred_tasks

    def _execute_todo_tasks(
        self, active_tasks: List[Dict[str, Any]]
    ) -> Tuple[int, List[str]]:
        """Execute TODO tasks and return count of fixed tasks and completed task lines."""
        config = self._get_refactoring_config()
        scanner = Scanner(config)
        fixer = Fixer(config)
        executed_count = 0
        completed_tasks = []

        # Group tasks by file to avoid scanning the same file multiple times
        tasks_by_file = self._group_tasks_by_file(active_tasks)

        # Process each file
        for file_path, file_tasks in tasks_by_file.items():
            if file_path.exists():
                try:
                    result = self._process_file_tasks(
                        file_path, file_tasks, scanner, fixer
                    )
                    executed_count += result["fixed_count"]
                    completed_tasks.extend(result["completed_tasks"])
                except Exception as e:
                    console.print(f"❌ Error fixing {file_path}: {str(e)}")
                    completed_tasks.extend(task["original_line"] for task in file_tasks)
            else:
                console.print(f"⚠️  File not found: {file_path}")
                completed_tasks.extend(task["original_line"] for task in file_tasks)

        return executed_count, completed_tasks

    def _group_tasks_by_file(
        self, active_tasks: List[Dict[str, Any]]
    ) -> Dict[Path, List[Dict[str, Any]]]:
        """Group tasks by file path."""
        tasks_by_file = {}
        for task in active_tasks:
            file_path = self.project_root / task["file"]
            if file_path not in tasks_by_file:
                tasks_by_file[file_path] = []
            tasks_by_file[file_path].append(task)
        return tasks_by_file

    def _process_file_tasks(
        self,
        file_path: Path,
        file_tasks: List[Dict[str, Any]],
        scanner: Scanner,
        fixer: Fixer,
    ) -> Dict[str, Any]:
        """Process tasks for a single file."""
        # Scan the file to get current issues
        issues_map = scanner.scan([file_path])
        issues = issues_map.get(file_path, [])

        completed_tasks = []
        fixed_count = 0

        if issues:
            # Fix the file with its issues
            fixed_source, fixes = fixer.fix_file(file_path, issues)
            if fixes:
                # Mark all tasks for this file as completed
                for task in file_tasks:
                    completed_tasks.append(
                        f"- [x] {task['file']}:{task['line']} - {task['message']} ✅"
                    )
                    fixed_count += 1
                    console.print(f"✅ Fixed: {task['file']}:{task['line']}")
            else:
                # Keep as active if not fixed
                completed_tasks.extend(task["original_line"] for task in file_tasks)
        else:
            # No issues found, keep as active
            completed_tasks.extend(task["original_line"] for task in file_tasks)

        return {"completed_tasks": completed_tasks, "fixed_count": fixed_count}

    def _update_todo_with_execution_results(
        self,
        completed_tasks: List[str],
        executed_count: int,
        processed_tasks: int,
        total_tasks: int,
    ) -> None:
        """Update the prefact block with execution results (manual content kept)."""
        block = build_execution_block(
            completed_tasks, executed_count, processed_tasks, total_tasks
        )
        self._write_owned_block(block)
        console.print(
            f"🎉 Execution complete: {processed_tasks}/{total_tasks} tasks processed, {executed_count} fixed"
        )
