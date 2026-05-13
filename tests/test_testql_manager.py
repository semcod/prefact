"""Tests for prefact TestQL integration via planfile API."""

import sys
import types
from pathlib import Path

import pytest


@pytest.fixture
def planfile_stub(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Install a stub `planfile` package exposing TestQL helpers."""
    calls: dict = {
        "run": [],
        "build": [],
        "upsert": [],
        "sync": [],
    }

    def fake_run_testql_validation(**kwargs):
        calls["run"].append(kwargs)
        return {
            "ok": False,
            "passed": 0,
            "failed": 1,
            "exit_code": 1,
            "source": "scenario.yaml",
            "errors": ["boom"],
            "warnings": [],
        }

    def fake_build_testql_tickets(report, scenario_path, max_tickets=25):
        calls["build"].append(
            {"report": report, "scenario": scenario_path, "max": max_tickets}
        )
        return [
            {
                "id": "TQL-x1",
                "title": "testql failure",
                "description": "d",
                "labels": ["testql"],
            }
        ]

    def fake_upsert_testql_tickets(strategy_path, tickets, project_path=None):
        calls["upsert"].append(
            {
                "strategy_path": strategy_path,
                "tickets": list(tickets),
                "project_path": project_path,
            }
        )
        return {
            "strategy_path": str(strategy_path),
            "created": len(tickets),
            "skipped": 0,
            "created_ticket_ids": [t["id"] for t in tickets],
        }

    def fake_sync_testql_tickets(tickets, project_path=None, include_configured=True):
        calls["sync"].append(
            {
                "tickets": list(tickets),
                "project_path": project_path,
                "include_configured": include_configured,
            }
        )
        return {
            "sync_order": ["markdown"],
            "integrations": [
                {
                    "integration": "markdown",
                    "created": len(tickets),
                    "updated": 0,
                    "skipped": 0,
                    "failed": 0,
                }
            ],
        }

    stub_module = types.ModuleType("planfile")
    stub_module.run_testql_validation = fake_run_testql_validation
    stub_module.build_testql_tickets = fake_build_testql_tickets
    stub_module.upsert_testql_tickets = fake_upsert_testql_tickets
    stub_module.sync_testql_tickets = fake_sync_testql_tickets

    monkeypatch.setitem(sys.modules, "planfile", stub_module)
    return calls


def test_run_testql_creates_and_syncs_tickets(
    tmp_path: Path, planfile_stub: dict
) -> None:
    from prefact.autonomous import AutonomousRefact

    auto = AutonomousRefact(tmp_path)
    scenario_path = tmp_path / "scenario.testql.toon.yaml"
    scenario_path.write_text("---\n", encoding="utf-8")

    payload = auto.run_testql(scenario_path=scenario_path)

    assert payload["validation"]["ok"] is False
    assert payload["validation"]["failed"] == 1
    assert payload["tickets"]["generated"] == 1
    assert payload["tickets"]["created"] == 1
    assert payload["tickets"]["created_ticket_ids"] == ["TQL-x1"]
    assert payload["tickets"]["sync"]["sync_order"] == ["markdown"]

    assert len(planfile_stub["run"]) == 1
    assert len(planfile_stub["build"]) == 1
    assert len(planfile_stub["upsert"]) == 1
    assert len(planfile_stub["sync"]) == 1


def test_run_testql_respects_no_create_tickets(
    tmp_path: Path, planfile_stub: dict
) -> None:
    from prefact.autonomous import AutonomousRefact

    auto = AutonomousRefact(tmp_path)
    scenario_path = tmp_path / "scenario.testql.toon.yaml"
    scenario_path.write_text("---\n", encoding="utf-8")

    payload = auto.run_testql(scenario_path=scenario_path, create_tickets=False)

    assert payload["tickets"]["generated"] == 0
    assert payload["tickets"]["created"] == 0
    assert payload["tickets"]["sync"] is None
    assert planfile_stub["build"] == []
    assert planfile_stub["upsert"] == []
    assert planfile_stub["sync"] == []


def test_discover_scenarios_returns_sorted_glob(tmp_path: Path) -> None:
    from prefact.autonomous import AutonomousRefact

    scenarios_dir = tmp_path / "testql-scenarios"
    scenarios_dir.mkdir()
    (scenarios_dir / "b.testql.toon.yaml").write_text("---\n", encoding="utf-8")
    (scenarios_dir / "a.testql.toon.yaml").write_text("---\n", encoding="utf-8")
    (scenarios_dir / "ignored.txt").write_text("x", encoding="utf-8")

    auto = AutonomousRefact(tmp_path)
    found = auto.testql_manager.discover_scenarios()

    assert [p.name for p in found] == ["a.testql.toon.yaml", "b.testql.toon.yaml"]


def test_run_testql_all_skips_when_no_scenarios(
    tmp_path: Path, planfile_stub: dict
) -> None:
    from prefact.autonomous import AutonomousRefact

    auto = AutonomousRefact(tmp_path)

    summary = auto.run_testql_all()

    assert summary["scenarios_found"] == 0
    assert summary["summary"]["ok"] is True
    assert planfile_stub["run"] == []


def test_run_testql_all_aggregates_results(tmp_path: Path, planfile_stub: dict) -> None:
    from prefact.autonomous import AutonomousRefact

    scenarios_dir = tmp_path / "testql-scenarios"
    scenarios_dir.mkdir()
    (scenarios_dir / "a.testql.toon.yaml").write_text("---\n", encoding="utf-8")
    (scenarios_dir / "b.testql.toon.yaml").write_text("---\n", encoding="utf-8")

    auto = AutonomousRefact(tmp_path)
    summary = auto.run_testql_all()

    assert summary["scenarios_found"] == 2
    assert summary["summary"]["failed"] == 2
    assert summary["summary"]["created"] == 2
    assert summary["summary"]["ok"] is False
    assert len(planfile_stub["run"]) == 2


def _stub_pipeline_steps(auto, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auto, "create_refact_config", lambda: None)
    monkeypatch.setattr(auto, "run_examples", lambda: True)
    monkeypatch.setattr(auto, "scan_project", lambda: None)
    monkeypatch.setattr(auto, "update_planfile", lambda: None)
    monkeypatch.setattr(auto, "manage_documentation", lambda: None)
    monkeypatch.setattr(auto.scanner, "get_autonomous_limit", lambda key: 10_000)


def test_run_autonomous_with_testql_invokes_run_all(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from prefact.autonomous import AutonomousRefact

    (tmp_path / "prefact.yaml").write_text("include: []\n", encoding="utf-8")

    auto = AutonomousRefact(tmp_path)
    calls: dict = {"all": []}

    _stub_pipeline_steps(auto, monkeypatch)
    monkeypatch.setattr(
        auto,
        "run_testql_all",
        lambda scenarios_dir=None: (
            calls["all"].append(scenarios_dir)
            or {
                "scenarios_found": 0,
                "scenarios": [],
                "summary": {"ok": True, "failed": 0, "created": 0, "skipped": 0},
            }
        ),
    )

    assert (
        auto.run_autonomous(
            skip_examples=True, with_testql=True, testql_scenarios_dir="custom"
        )
        is True
    )
    assert calls["all"] == ["custom"]


def test_run_autonomous_default_skips_testql(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from prefact.autonomous import AutonomousRefact

    (tmp_path / "prefact.yaml").write_text("include: []\n", encoding="utf-8")

    auto = AutonomousRefact(tmp_path)
    calls: dict = {"all": 0}

    _stub_pipeline_steps(auto, monkeypatch)

    def fail_all(*_args, **_kwargs):
        calls["all"] += 1
        return {}

    monkeypatch.setattr(auto, "run_testql_all", fail_all)

    assert auto.run_autonomous(skip_examples=True) is True
    assert calls["all"] == 0
