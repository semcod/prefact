"""Tests for the CQRS + Event Sourcing foundation."""

from pathlib import Path

from prefact.config import Config
from prefact.cqrs import (
    AnalysisQueryHandler,
    EventBus,
    FixApplied,
    FixFailed,
    FixFile,
    InMemoryEventStore,
    IssueDetected,
    JsonlEventStore,
    PipelineStarted,
    RefactoringCommandHandler,
    ScanCompleted,
    ScanStarted,
    ValidateFile,
)
from prefact.cqrs.events import from_dict
from prefact.engine import RefactoringEngine
from prefact.models import Fix, Issue, ValidationResult

# ── event bus ──────────────────────────────────────────────────────────


def test_bus_dispatches_to_subscribers() -> None:
    bus = EventBus()
    seen: list[ScanStarted] = []
    bus.subscribe("analysis.scan.started", lambda event: seen.append(event))
    bus.publish(ScanStarted(file_count=2))
    assert len(seen) == 1
    assert seen[0].file_count == 2


def test_bus_persists_to_attached_store() -> None:
    store = InMemoryEventStore()
    bus = EventBus(store=store)
    bus.publish(PipelineStarted(dry_run=True))
    assert len(store.load()) == 1
    assert isinstance(store.load()[0], PipelineStarted)


def test_bus_unsubscribe() -> None:
    bus = EventBus()
    seen: list[ScanStarted] = []
    handler = lambda event: seen.append(event)  # noqa: E731
    bus.subscribe("analysis.scan.started", handler)
    bus.unsubscribe("analysis.scan.started", handler)
    bus.publish(ScanStarted(file_count=1))
    assert seen == []


# ── event stores ───────────────────────────────────────────────────────


def test_in_memory_store_is_append_only() -> None:
    store = InMemoryEventStore()
    store.append(ScanStarted(file_count=1))
    store.append(ScanCompleted(file_count=1, issue_count=0))
    assert len(store.load()) == 2


def test_jsonl_store_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    store = JsonlEventStore(path)
    store.append(ScanCompleted(file_count=2, issue_count=3))
    store.append(
        IssueDetected(
            rule_id="r", file="f.py", line=1, col=2, message="m", severity="error"
        )
    )
    events = store.load()
    assert isinstance(events[0], ScanCompleted)
    assert events[0].issue_count == 3
    assert events[1].severity == "error"


def test_event_serialization_round_trip() -> None:
    event = IssueDetected(
        rule_id="r", file="f.py", line=1, col=2, message="m", severity="warning"
    )
    rebuilt = from_dict(event.to_dict())
    assert rebuilt == event


# ── command handler ────────────────────────────────────────────────────


class _FakeFixer:
    def fix_file_with_source(
        self,
        path: Path,
        source: str,
        issues: list[Issue],
        *,
        dry_run: bool = False,
    ) -> tuple[str, list[Fix]]:
        applied = issues[0].rule_id != "failing"
        fix = Fix(
            issue=issues[0],
            file=path,
            original_code=source,
            fixed_code=source,
            applied=applied,
            error=None if applied else "boom",
        )
        return source, [fix]


def _issue(rule_id: str = "r") -> Issue:
    return Issue(rule_id=rule_id, file=Path("f.py"), line=1, col=1, message="m")


def test_command_handler_emits_fix_applied() -> None:
    bus = EventBus()
    handler = RefactoringCommandHandler(_FakeFixer(), bus)
    seen: list[FixApplied] = []
    bus.subscribe("refactoring.fix.applied", lambda event: seen.append(event))

    issue = _issue()
    _source, fixes = handler.handle(
        FixFile(path=Path("f.py"), source="x", issues=[issue])
    )
    assert fixes[0].applied is True
    assert len(seen) == 1
    assert seen[0].rule_id == "r"


def test_command_handler_emits_fix_failed() -> None:
    bus = EventBus()
    handler = RefactoringCommandHandler(_FakeFixer(), bus)
    seen: list[FixFailed] = []
    bus.subscribe("refactoring.fix.failed", lambda event: seen.append(event))

    issue = _issue(rule_id="failing")
    handler.handle(FixFile(path=Path("f.py"), source="x", issues=[issue]))
    assert len(seen) == 1
    assert seen[0].error == "boom"


def test_command_handler_rejects_unknown_command() -> None:
    import pytest

    from prefact.cqrs.commands.base import Command

    bus = EventBus()
    handler = RefactoringCommandHandler(_FakeFixer(), bus)
    with pytest.raises(TypeError):
        handler.handle(Command())


# ── query handler ──────────────────────────────────────────────────────


class _FakeScanner:
    def scan_sources(self, sources: dict[Path, str]) -> dict[Path, list[Issue]]:
        return {path: [_issue()] for path in sources}


class _FakeValidator:
    def validate_file(
        self, path: Path, original: str, fixed: str, issues: list[Issue]
    ) -> list[ValidationResult]:
        return [ValidationResult(file=path, passed=True)]


def test_query_handler_emits_scan_events() -> None:
    bus = EventBus()
    handler = AnalysisQueryHandler(_FakeScanner(), _FakeValidator(), bus)
    started: list[ScanStarted] = []
    detected: list[IssueDetected] = []
    completed: list[ScanCompleted] = []
    bus.subscribe("analysis.scan.started", lambda event: started.append(event))
    bus.subscribe("analysis.issue.detected", lambda event: detected.append(event))
    bus.subscribe("analysis.scan.completed", lambda event: completed.append(event))

    from prefact.cqrs.queries.analysis import ScanSources

    results = handler.handle(ScanSources(sources={Path("f.py"): "x"}))
    assert len(results[Path("f.py")]) == 1
    assert len(started) == 1
    assert len(detected) == 1
    assert len(completed) == 1
    assert completed[0].issue_count == 1


def test_query_handler_emits_validation_event() -> None:
    bus = EventBus()
    handler = AnalysisQueryHandler(_FakeScanner(), _FakeValidator(), bus)
    seen: list[object] = []
    bus.subscribe("analysis.validation.completed", lambda event: seen.append(event))

    results = handler.handle(
        ValidateFile(
            path=Path("f.py"), original="a", fixed="b", issues=[_issue()]
        )
    )
    assert results[0].passed is True
    assert len(seen) == 1


def test_query_handler_rejects_unknown_query() -> None:
    import pytest

    from prefact.cqrs.queries.base import Query

    bus = EventBus()
    handler = AnalysisQueryHandler(_FakeScanner(), _FakeValidator(), bus)
    with pytest.raises(TypeError):
        handler.handle(Query())


# ── engine wiring ──────────────────────────────────────────────────────


def test_engine_exposes_bus_and_store() -> None:
    engine = RefactoringEngine(Config())
    assert isinstance(engine.store, InMemoryEventStore)
    assert engine.bus.store is engine.store


def test_engine_persists_to_configured_store(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    engine = RefactoringEngine(Config(event_store=path))
    engine.bus.publish(PipelineStarted(dry_run=True))
    assert len(engine.store.load()) == 1
    assert path.exists()
