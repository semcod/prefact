"""Tests for autonomous mode limits and batching."""


from pathlib import Path
from typing import Any

import yaml

from prefact.autonomous.docs_manager import DocsManager
from prefact.autonomous import AutonomousRefact
from prefact.autonomous.project_scanner import ProjectScanner
from prefact.autonomous.todo_manager import TodoManager
from prefact.config_extended import ConfigGenerator, ConfigValidator, ExtendedConfig
from prefact.models import Issue, Severity


def _write_prefact_config(project_root: Path, performance: dict[str, Any]) -> None:
    config = {"performance": performance}
    (project_root / "prefact.yaml").write_text(yaml.safe_dump(config, sort_keys=False))


def _issue_group(file_path: Path, rule_id: str, example_count: int = 1) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "file": str(file_path),
        "count": example_count,
        "severity": "warning",
        "examples": [
            {"line": line_number, "message": f"issue {line_number}"}
            for line_number in range(1, example_count + 1)
        ],
    }


def test_config_generator_includes_autonomous_limits(tmp_path: Path) -> None:
    config_text = ConfigGenerator.generate_extended_config(tmp_path)
    config = yaml.safe_load(config_text)

    assert config["performance"]["autonomous_max_examples_per_issue"] == 3
    assert config["performance"]["autonomous_max_tickets"] == 100
    assert config["performance"]["autonomous_max_todo_items"] == 200
    assert config["performance"]["autonomous_max_completed_todos"] == 100
    assert config["performance"]["autonomous_max_todo_execution_items"] == 50



def test_config_validator_rejects_invalid_autonomous_limits(tmp_path: Path) -> None:
    config = ExtendedConfig(
        project_root=tmp_path,
        performance={
            "autonomous_max_tickets": 0,
            "autonomous_max_todo_items": -1,
        },
    )

    errors = ConfigValidator.validate(config)

    assert "performance.autonomous_max_tickets must be a positive integer" in errors
    assert "performance.autonomous_max_todo_items must be a positive integer" in errors



def test_project_scanner_respects_configured_example_limit(tmp_path: Path) -> None:
    _write_prefact_config(tmp_path, {"autonomous_max_examples_per_issue": 1})
    scanner = ProjectScanner(tmp_path)
    file_path = tmp_path / "module.py"

    issues = [
        Issue("demo-rule", file_path, 1, 1, "first", Severity.WARNING),
        Issue("demo-rule", file_path, 2, 1, "second", Severity.WARNING),
    ]

    grouped = scanner.group_issues(issues)

    assert len(grouped) == 1
    assert grouped[0]["count"] == 2
    assert len(grouped[0]["examples"]) == 1
    assert grouped[0]["examples"][0]["message"] == "first"



def test_project_scanner_caps_files_to_scan(tmp_path: Path) -> None:
    _write_prefact_config(tmp_path, {"autonomous_max_files_to_scan": 1})
    first_file = tmp_path / "first.py"
    second_file = tmp_path / "second.py"
    first_file.write_text("print('one')\n")
    second_file.write_text("print('two')\n")

    scanner = ProjectScanner(tmp_path)
    collected = []

    class DummyScanner:
        def collect_files(self):
            return [first_file, second_file]

    scanner._scan_files_with_progress = lambda _scanner, files, _config: collected.extend(files) or []  # type: ignore[method-assign]
    scanner.scan_project = ProjectScanner.scan_project.__get__(scanner, ProjectScanner)

    original_scanner_cls = __import__("prefact.autonomous.project_scanner", fromlist=["Scanner"]).Scanner
    try:
        __import__("prefact.autonomous.project_scanner", fromlist=["Scanner"]).Scanner = lambda config: DummyScanner()  # type: ignore[assignment]
        scanner.scan_project()
    finally:
        __import__("prefact.autonomous.project_scanner", fromlist=["Scanner"]).Scanner = original_scanner_cls  # type: ignore[assignment]

    assert collected == [first_file]


def test_project_scanner_caps_issues_per_file(tmp_path: Path) -> None:
    _write_prefact_config(tmp_path, {"autonomous_max_issues_per_file": 1})
    scanner = ProjectScanner(tmp_path)
    file_path = tmp_path / "module.py"

    issues = [
        Issue("demo-rule", file_path, 1, 1, "first", Severity.WARNING),
        Issue("demo-rule", file_path, 2, 1, "second", Severity.WARNING),
    ]

    grouped = scanner.group_issues(issues)

    assert len(grouped) == 1
    assert grouped[0]["count"] == 1
    assert grouped[0]["examples"][0]["message"] == "first"


def test_autonomous_refact_caps_grouped_issues_before_distribution(tmp_path: Path) -> None:
    _write_prefact_config(tmp_path, {"autonomous_max_issues": 1})
    refact = AutonomousRefact(tmp_path)
    refact.scanner.scan_project = lambda: [
        Issue("demo-rule", tmp_path / "a.py", 1, 1, "first", Severity.WARNING),
        Issue("demo-rule", tmp_path / "b.py", 2, 1, "second", Severity.WARNING),
    ]  # type: ignore[method-assign]

    refact.scan_project()

    assert len(refact.issues_found) == 1
    assert refact.todo_manager.issues_found == refact.issues_found
    assert refact.docs_manager.issues_found == refact.issues_found


def test_autonomous_refact_stops_before_docs_when_time_limit_exceeded(tmp_path: Path) -> None:
    _write_prefact_config(tmp_path, {"autonomous_max_run_seconds": 1})
    refact = AutonomousRefact(tmp_path)

    refact.run_examples = lambda: True  # type: ignore[method-assign]
    refact.scan_project = lambda: None  # type: ignore[method-assign]

    called = {"planfile": False, "docs": False}

    def fail_planfile() -> None:
        called["planfile"] = True

    def fail_docs() -> None:
        called["docs"] = True

    refact.update_planfile = fail_planfile  # type: ignore[method-assign]
    refact.manage_documentation = fail_docs  # type: ignore[method-assign]

    import prefact.autonomous as autonomous_module

    original_monotonic = autonomous_module.monotonic
    try:
        times = iter([0.0, 1.0])
        autonomous_module.monotonic = lambda: next(times)  # type: ignore[assignment]

        assert refact.run_autonomous() is False
        assert called == {"planfile": False, "docs": False}
    finally:
        autonomous_module.monotonic = original_monotonic  # type: ignore[assignment]


def test_autonomous_refact_prints_final_summary(tmp_path: Path, capsys) -> None:
    _write_prefact_config(tmp_path, {"autonomous_max_run_seconds": 1})
    refact = AutonomousRefact(tmp_path)

    refact.run_examples = lambda: True  # type: ignore[method-assign]
    refact.scan_project = lambda: None  # type: ignore[method-assign]
    refact.update_planfile = lambda: None  # type: ignore[method-assign]
    refact.manage_documentation = lambda: None  # type: ignore[method-assign]

    import prefact.autonomous as autonomous_module

    original_monotonic = autonomous_module.monotonic
    try:
        autonomous_module.monotonic = lambda: 0.0  # type: ignore[assignment]
        assert refact.run_autonomous() is True
    finally:
        autonomous_module.monotonic = original_monotonic  # type: ignore[assignment]

    output = capsys.readouterr().out
    assert "Autonomous summary:" in output


def test_docs_manager_respects_total_ticket_limit(tmp_path: Path) -> None:
    _write_prefact_config(tmp_path, {"autonomous_max_tickets": 2})
    planfile = {
        "sprints": [
            {
                "id": "sprint-1",
                "task_patterns": [
                    {
                        "id": "ticket-existing",
                        "rule_id": "existing-rule",
                        "files": ["existing.py"],
                    }
                ],
            }
        ]
    }
    (tmp_path / "planfile.yaml").write_text(yaml.safe_dump(planfile, sort_keys=False))

    manager = DocsManager(tmp_path)
    manager.issues_found = [
        _issue_group(tmp_path / "a.py", "rule-a"),
        _issue_group(tmp_path / "b.py", "rule-b"),
        _issue_group(tmp_path / "c.py", "rule-c"),
    ]

    manager.update_planfile()

    updated = yaml.safe_load((tmp_path / "planfile.yaml").read_text())
    task_patterns = updated["sprints"][0]["task_patterns"]

    assert len(task_patterns) == 2
    assert len(manager.tickets_created) == 1
    assert task_patterns[-1]["rule_id"] == "rule-a"


def test_docs_manager_reports_skipped_ticket_count(tmp_path: Path, capsys) -> None:
    _write_prefact_config(tmp_path, {"autonomous_max_tickets": 1})
    manager = DocsManager(tmp_path)
    manager.issues_found = [
        _issue_group(tmp_path / "a.py", "rule-a"),
        _issue_group(tmp_path / "b.py", "rule-b"),
    ]

    manager.update_planfile()

    output = capsys.readouterr().out
    assert "skipping 1 remaining autonomous tickets" in output
    assert "1 issue groups skipped by limit" in output


def test_todo_manager_reports_skipped_todo_counts(tmp_path: Path, capsys) -> None:
    _write_prefact_config(
        tmp_path,
        {
            "autonomous_max_todo_items": 1,
            "autonomous_max_completed_todos": 1,
            "autonomous_max_todo_execution_items": 1,
        },
    )
    current_file = tmp_path / "pkg" / "module.py"
    current_file.parent.mkdir(parents=True)
    current_file.write_text("print('demo')\n")
    (tmp_path / "TODO.md").write_text(
        "# TODO\n\n"
        "## 📋 Current Issues\n\n"
        f"- [ ] {current_file}:1 - issue 1\n"
        "- [ ] other.py:1 - issue 2\n"
        "## ✅ Completed Tasks\n\n"
        "- [ ] old.py:1 - old issue\n"
        "- [ ] old.py:2 - old issue 2\n"
    )

    manager = TodoManager(tmp_path)
    manager.issues_found = [_issue_group(current_file, "rule-a", example_count=2)]

    manager.update_todo_md()

    output = capsys.readouterr().out
    assert "omitting 1 remaining active issues" in output
    assert "omitting 1 remaining completed tasks" in output



def test_todo_manager_limits_output_and_normalizes_existing_paths(tmp_path: Path) -> None:
    _write_prefact_config(
        tmp_path,
        {
            "autonomous_max_todo_items": 2,
            "autonomous_max_completed_todos": 1,
        },
    )
    current_file = tmp_path / "pkg" / "module.py"
    current_file.parent.mkdir(parents=True)
    current_file.write_text("print('demo')\n")
    (tmp_path / "TODO.md").write_text(
        "# TODO\n\n"
        "## 📋 Current Issues\n\n"
        f"- [ ] {current_file}:1 - issue 1\n"
        "- [ ] old.py:1 - old 1\n"
        "- [ ] old.py:2 - old 2\n"
    )

    manager = TodoManager(tmp_path)
    manager.issues_found = [_issue_group(current_file, "rule-a", example_count=3)]

    manager.update_todo_md()

    content = (tmp_path / "TODO.md").read_text()

    assert content.count("- [ ] ") == 2
    assert content.count("- [x] ") == 1
    assert "## ✅ Completed Tasks (showing 1 of 2)" in content
    assert "## 📋 Current Issues (showing 2 of 3)" in content
    assert f"- [x] {current_file}:1 - issue 1" not in content



def test_todo_manager_execute_todos_respects_execution_limit(tmp_path: Path) -> None:
    _write_prefact_config(tmp_path, {"autonomous_max_todo_execution_items": 2})
    (tmp_path / "TODO.md").write_text(
        "# TODO\n\n"
        "## 📋 Current Issues\n\n"
        "- [ ] a.py:1 - first\n"
        "- [ ] a.py:2 - second\n"
        "- [ ] a.py:3 - third\n"
    )

    manager = TodoManager(tmp_path)
    captured: dict[str, Any] = {}

    def fake_execute(tasks: list[dict[str, Any]]) -> tuple[int, list[str]]:
        captured["tasks"] = tasks
        return 1, [
            "- [x] a.py:1 - first ✅",
            "- [ ] a.py:2 - second",
        ]

    manager._execute_todo_tasks = fake_execute  # type: ignore[method-assign]

    manager.execute_todos()

    content = (tmp_path / "TODO.md").read_text()

    assert len(captured["tasks"]) == 2
    assert "- [ ] a.py:3 - third" in content
    assert "**Total issues:** 2 processed of 3 active, 1 fixed" in content
