"""Tests for prefact.autonomous.docs_manager.DocsManager."""

from pathlib import Path

from prefact.autonomous.docs_manager import DocsManager


def _issue_group(rule_id: str, file: str, count: int = 1, severity: str = "warning"):
    return {"rule_id": rule_id, "file": file, "count": count, "severity": severity}


def test_detect_project_version_reads_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "1.2.3"\n', encoding="utf-8"
    )
    manager = DocsManager(tmp_path)
    assert manager._detect_project_version() == "1.2.3"


def test_detect_project_version_falls_back_without_pyproject(tmp_path: Path) -> None:
    manager = DocsManager(tmp_path)
    assert manager._detect_project_version() == "Unreleased"


def test_detect_project_version_falls_back_without_version_field(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")
    manager = DocsManager(tmp_path)
    assert manager._detect_project_version() == "Unreleased"


def test_update_changelog_md_uses_detected_version_not_hardcoded(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "9.9.9"\n', encoding="utf-8"
    )
    manager = DocsManager(tmp_path)
    manager.tickets_created = [
        {"name": "Fix foo issues", "id": "ticket-abc12345"},
    ]

    manager.update_changelog_md()

    content = manager.changelog_path.read_text(encoding="utf-8")
    assert "## [9.9.9]" in content
    assert "0.1.10" not in content


def test_update_planfile_creates_tickets_from_issues(tmp_path: Path) -> None:
    manager = DocsManager(tmp_path)
    manager.issues_found = [_issue_group("unused-imports", "src/a.py", count=3)]

    manager.update_planfile()

    assert len(manager.tickets_created) == 1
    assert manager.tickets_created[0]["rule_id"] == "unused-imports"
    assert manager.planfile_path.exists()


def test_update_planfile_deduplicates_across_issue_groups(tmp_path: Path) -> None:
    manager = DocsManager(tmp_path)
    manager.issues_found = [
        _issue_group("unused-imports", "src/a.py"),
        _issue_group("unused-imports", "src/a.py"),
    ]

    manager.update_planfile()

    assert len(manager.tickets_created) == 1


def test_update_planfile_removes_obsolete_tickets(tmp_path: Path) -> None:
    manager = DocsManager(tmp_path)
    manager.issues_found = [_issue_group("unused-imports", "src/a.py")]
    manager.update_planfile()
    assert len(manager.tickets_created) == 1

    # Re-run with the issue gone: the previously-created autonomous ticket
    # for it must be cleaned up rather than lingering forever.
    manager2 = DocsManager(tmp_path)
    manager2.issues_found = []
    manager2.update_planfile()

    import yaml

    planfile = yaml.safe_load(manager.planfile_path.read_text())
    all_tickets = list(planfile.get("backlog", []))
    for sprint in planfile.get("sprints", []):
        all_tickets.extend(sprint.get("tasks", []))
        all_tickets.extend(sprint.get("task_patterns", []))
    assert all_tickets == []


def test_update_planfile_respects_ticket_limit(tmp_path: Path, monkeypatch) -> None:
    manager = DocsManager(tmp_path)
    monkeypatch.setattr(manager, "get_autonomous_limit", lambda key: 1)
    manager.issues_found = [
        _issue_group("rule-a", "src/a.py"),
        _issue_group("rule-b", "src/b.py"),
    ]

    manager.update_planfile()

    assert len(manager.tickets_created) == 1
