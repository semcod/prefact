"""TestQL integration manager for autonomous prefact runs.

Delegates execution, ticket generation, upsert into ``planfile.yaml``, and sync
to TODO.md plus configured integrations to the shared ``planfile`` API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from prefact.autonomous._base import BaseManager, console

DEFAULT_SCENARIOS_DIR = "testql-scenarios"
SCENARIO_GLOB = "*.testql.toon.yaml"


class TestQLManager(BaseManager):
    """Run TestQL DSL validation and bridge results into planfile."""

    def run(
        self,
        scenario_path: str | Path,
        *,
        url: str = "http://localhost:8101",
        dry_run: bool = False,
        create_tickets: bool = True,
        sync_targets: bool = True,
        max_tickets: int = 25,
        testql_bin: str = "testql",
        testql_repo_path: str | Path = "/home/tom/github/oqlos/testql",
        strategy_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Execute scenario and update planfile/TODO based on results.

        Returns a structured payload with validation report, tickets summary,
        and per-integration sync status. Network/LLM operations are delegated
        to ``planfile.testql_integration``.
        """
        try:
            from planfile import (
                build_testql_tickets,  # noqa: F401 - import-guards the exc branch below
                run_testql_validation,
                sync_testql_tickets,  # noqa: F401
                upsert_testql_tickets,  # noqa: F401
            )
        except ImportError as exc:  # pragma: no cover - dependency missing
            raise ImportError(
                "planfile>=0.1.85 is required for TestQL integration"
            ) from exc

        strategy = str(strategy_path or self.planfile_path)

        validation = run_testql_validation(
            scenario_path=scenario_path,
            project_path=self.project_root,
            url=url,
            dry_run=dry_run,
            quiet=True,
            testql_bin=testql_bin,
            testql_repo_path=testql_repo_path,
        )

        payload: dict[str, Any] = {
            "scenario": str(scenario_path),
            "strategy": strategy,
            "project": str(self.project_root),
            "validation": {
                "ok": bool(validation.get("ok")),
                "passed": int(validation.get("passed") or 0),
                "failed": int(validation.get("failed") or 0),
                "exit_code": int(validation.get("exit_code") or 0),
                "source": validation.get("source"),
                "errors": validation.get("errors") or [],
                "warnings": validation.get("warnings") or [],
            },
            "tickets": {
                "generated": 0,
                "created": 0,
                "skipped": 0,
                "created_ticket_ids": [],
                "sync": None,
            },
        }

        if not bool(validation.get("ok")) and create_tickets:
            self._create_and_sync_tickets(
                validation,
                scenario_path=scenario_path,
                max_tickets=max_tickets,
                strategy=strategy,
                sync_targets=sync_targets,
                payload=payload,
            )

        console.print(
            f"🧪 TestQL: ok={payload['validation']['ok']} "
            f"passed={payload['validation']['passed']} "
            f"failed={payload['validation']['failed']}"
        )
        console.print(
            f"🎫 Tickets: generated={payload['tickets']['generated']} "
            f"created={payload['tickets']['created']} "
            f"skipped={payload['tickets']['skipped']}"
        )

        return payload

    def _create_and_sync_tickets(
        self,
        validation: dict[str, Any],
        *,
        scenario_path: str | Path,
        max_tickets: int,
        strategy: str,
        sync_targets: bool,
        payload: dict[str, Any],
    ) -> None:
        """Build tickets from a failed validation, upsert them, and sync them.

        Mutates ``payload["tickets"]`` in place; only called once ``run()``
        already imported the ``planfile`` integration successfully.
        """
        from planfile import (
            build_testql_tickets,
            sync_testql_tickets,
            upsert_testql_tickets,
        )

        tickets = build_testql_tickets(
            validation,
            scenario_path=scenario_path,
            max_tickets=max_tickets,
        )
        payload["tickets"]["generated"] = len(tickets)

        if not tickets:
            return

        upsert_report = upsert_testql_tickets(
            strategy_path=strategy,
            tickets=tickets,
            project_path=self.project_root,
        )
        payload["tickets"]["created"] = int(upsert_report.get("created") or 0)
        payload["tickets"]["skipped"] = int(upsert_report.get("skipped") or 0)
        payload["tickets"]["created_ticket_ids"] = (
            upsert_report.get("created_ticket_ids") or []
        )

        if sync_targets:
            payload["tickets"]["sync"] = sync_testql_tickets(
                tickets,
                project_path=self.project_root,
                include_configured=True,
            )

    def discover_scenarios(
        self,
        scenarios_dir: str | Path | None = None,
    ) -> list[Path]:
        """Return sorted list of TestQL scenarios found in the project."""
        base = (
            Path(scenarios_dir)
            if scenarios_dir
            else self.project_root / DEFAULT_SCENARIOS_DIR
        )
        if not base.is_absolute():
            base = (self.project_root / base).resolve()
        if not base.exists() or not base.is_dir():
            return []
        return sorted(base.glob(SCENARIO_GLOB))

    def run_all(
        self,
        *,
        scenarios_dir: str | Path | None = None,
        url: str = "http://localhost:8101",
        dry_run: bool = False,
        create_tickets: bool = True,
        sync_targets: bool = True,
        max_tickets: int = 25,
        testql_bin: str = "testql",
        testql_repo_path: str | Path = "/home/tom/github/oqlos/testql",
        strategy_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Run all discovered TestQL scenarios and aggregate the results."""
        scenarios = self.discover_scenarios(scenarios_dir)
        results: list[dict[str, Any]] = []

        if not scenarios:
            console.print(
                "\u26a0\ufe0f No TestQL scenarios found; skipping TestQL step.",
                style="yellow",
            )
            return {
                "scenarios_found": 0,
                "scenarios": [],
                "summary": {
                    "ok": True,
                    "failed": 0,
                    "created": 0,
                    "skipped": 0,
                },
            }

        aggregate_failed = 0
        aggregate_created = 0
        aggregate_skipped = 0
        any_failed = False

        for scenario in scenarios:
            try:
                payload = self.run(
                    scenario_path=scenario,
                    url=url,
                    dry_run=dry_run,
                    create_tickets=create_tickets,
                    sync_targets=sync_targets,
                    max_tickets=max_tickets,
                    testql_bin=testql_bin,
                    testql_repo_path=testql_repo_path,
                    strategy_path=strategy_path,
                )
            except Exception as exc:  # pragma: no cover - resilience
                console.print(f"\u274c TestQL error on {scenario}: {exc}", style="red")
                results.append({"scenario": str(scenario), "error": str(exc)})
                any_failed = True
                continue

            results.append(payload)
            if not payload["validation"]["ok"]:
                any_failed = True
            aggregate_failed += int(payload["validation"].get("failed") or 0)
            aggregate_created += int(payload["tickets"].get("created") or 0)
            aggregate_skipped += int(payload["tickets"].get("skipped") or 0)

        return {
            "scenarios_found": len(scenarios),
            "scenarios": results,
            "summary": {
                "ok": not any_failed,
                "failed": aggregate_failed,
                "created": aggregate_created,
                "skipped": aggregate_skipped,
            },
        }


__all__ = ["TestQLManager", "DEFAULT_SCENARIOS_DIR", "SCENARIO_GLOB"]
