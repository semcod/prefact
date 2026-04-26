"""Tests for prefact TestQL integration via planfile API."""

from __future__ import annotations

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
        calls["build"].append({"report": report, "scenario": scenario_path, "max": max_tickets})
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


def test_run_testql_creates_and_syncs_tickets(tmp_path: Path, planfile_stub: dict) -> None:
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


def test_run_testql_respects_no_create_tickets(tmp_path: Path, planfile_stub: dict) -> None:
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
