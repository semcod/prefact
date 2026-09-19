"""Derive todo state from the prefact-owned block of TODO.md.

Parsing, current-issue derivation and completion detection operate only on
the owned region produced by :mod:`prefact.autonomous.todo_ownership` —
checkbox lines in manual sections are the operator's, not tickets prefact
created, and must never be adopted, completed, or garbage-collected here.
"""

from typing import Any, Callable, Dict, List, Set, Tuple

from ._base import console

CHECKBOX_PREFIX_LEN = 6  # len("- [ ] ") == len("- [x] ")


def parse_existing_todos(
    owned: str, relativize: Callable[[str], str]
) -> Tuple[Dict[Tuple, Dict[str, Any]], List[str]]:
    """Parse prefact-owned TODO entries from the owned block text.

    ``relativize`` converts absolute file paths to project-relative ones.
    """
    existing_todos: Dict[Tuple, Dict[str, Any]] = {}
    completed_todos: List[str] = []

    if not owned.strip():
        return existing_todos, completed_todos

    lines = owned.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("- [ ] ") or line.startswith("- [x] "):
            content = line[CHECKBOX_PREFIX_LEN:]

            # Handle multi-line messages
            while (
                i + 1 < len(lines)
                and not lines[i + 1].strip().startswith("- [")
                and lines[i + 1].strip()
            ):
                content += f" {lines[i + 1].strip()}"
                i += 1

            if " - " in content:
                file_line_part = content.split(" - ", 1)[0]
                message_part = content.split(" - ", 1)[1]
                status = "completed" if line.startswith("- [x] ") else "pending"

                # Parse file and line
                if ":" in file_line_part:
                    file_part = relativize(file_line_part.rsplit(":", 1)[0])
                    line_part = file_line_part.rsplit(":", 1)[1]
                    try:
                        line_num = int(line_part)
                        key = (file_part, line_num, message_part)
                    except ValueError:
                        # Line number is not an integer, treat differently
                        key = (file_part, message_part)
                    existing_todos[key] = {
                        "status": status,
                        "original_line": line,
                    }
        i += 1

    return existing_todos, completed_todos


def generate_current_todos(
    issues_found: List[Dict[str, Any]],
    existing_todos: Dict[Tuple, Dict[str, Any]],
    max_todo_items: int,
    relativize: Callable[[str], str],
) -> Tuple[Set[Tuple], List[str], int]:
    """Generate todo lines for current issues, honouring the output limit."""
    current_issues: Set[Tuple] = set()
    new_todos: List[str] = []
    seen: Set[Tuple] = set()
    total_active_todos = 0
    limit_reached = False
    skipped_active_todos = 0

    for issue_group in issues_found:
        rel_file = relativize(issue_group["file"])
        for example in issue_group["examples"]:
            key = (rel_file, example["line"], example["message"])
            current_issues.add(key)

            # Check if this is a new issue or existing one
            if key in existing_todos:
                # Keep existing status
                status = existing_todos[key]["status"]
                checkbox = "[x]" if status == "completed" else "[ ]"
            else:
                # New issue
                checkbox = "[ ]"

            # Avoid duplicates
            if key not in seen:
                total_active_todos += 1
                if len(new_todos) < max_todo_items:
                    new_todos.append(
                        f"- {checkbox} {rel_file}:{example['line']} - {example['message']}"
                    )
                elif not limit_reached:
                    skipped_active_todos = total_active_todos - len(new_todos)
                    console.print(
                        f"⚠️ TODO item limit reached ({max_todo_items}); omitting {max(0, skipped_active_todos)} remaining active issues from TODO.md.",
                        style="yellow",
                    )
                    limit_reached = True
                seen.add(key)

    return current_issues, new_todos, total_active_todos


def find_completed_tasks(
    existing_todos: Dict[Tuple, Dict[str, Any]],
    current_issues: Set[Tuple],
    max_completed_todos: int,
) -> Tuple[List[str], int]:
    """Find pending tasks that no longer have a current issue."""
    completed_tasks: List[str] = []
    total_completed_todos = 0
    limit_reached = False
    skipped_completed_todos = 0

    for key, todo_info in existing_todos.items():
        if key not in current_issues and todo_info["status"] == "pending":
            total_completed_todos += 1
            if len(completed_tasks) < max_completed_todos:
                completed_tasks.append(
                    f"- [x] {todo_info['original_line'][CHECKBOX_PREFIX_LEN:]}"
                )
            elif not limit_reached:
                skipped_completed_todos = total_completed_todos - len(
                    completed_tasks
                )
                console.print(
                    f"⚠️ Completed TODO limit reached ({max_completed_todos}); omitting {max(0, skipped_completed_todos)} remaining completed tasks from TODO.md.",
                    style="yellow",
                )
                limit_reached = True

    return completed_tasks, total_completed_todos


def parse_todo_tasks(owned: str) -> List[Dict[str, Any]]:
    """Parse active tasks from the prefact-owned block text."""
    lines = owned.split("\n")

    active_tasks: List[Dict[str, Any]] = []
    in_current_section = False

    for line in lines:
        if line.strip().startswith("## 📋 Current Issues"):
            in_current_section = True
            continue
        elif line.strip().startswith("##") and in_current_section:
            in_current_section = False
            continue
        elif in_current_section and line.strip().startswith("- [ ]"):
            task_line = line.strip()[CHECKBOX_PREFIX_LEN:]
            if " - " in task_line:
                file_line_part = task_line.split(" - ")[0]
                message = task_line.split(" - ", 1)[1]

                if ":" in file_line_part:
                    file_path = file_line_part.rsplit(":", 1)[0]
                    line_num = int(file_line_part.rsplit(":", 1)[1])
                    active_tasks.append(
                        {
                            "file": file_path,
                            "line": line_num,
                            "message": message,
                            "original_line": line,
                        }
                    )

    return active_tasks
