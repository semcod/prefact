"""TestQL integration manager for autonomous prefact runs.

Delegates execution, ticket generation, upsert into ``planfile.yaml``, and sync
to TODO.md plus configured integrations to the shared ``planfile`` API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from prefact.autonomous._base import BaseManager, console


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
                build_testql_tickets,
                run_testql_validation,
                sync_testql_tickets,
                upsert_testql_tickets,
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
            tickets = build_testql_tickets(
                validation,
                scenario_path=scenario_path,
                max_tickets=max_tickets,
            )
            payload["tickets"]["generated"] = len(tickets)

            if tickets:
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


__all__ = ["TestQLManager"]
