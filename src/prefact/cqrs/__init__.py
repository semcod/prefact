"""CQRS + Event Sourcing foundation for prefact.

prefact is organised around two bounded contexts, mapped onto the Command/Query
sides of the pipeline:

* ``analysis`` (query side) — reads the project tree and produces findings. It
  answers questions (``collect files``, ``scan``, ``validate``) and never
  mutates the codebase.
* ``refactoring`` (command side) — applies fixes to files. It expresses intent
  to change state (``fix file``) and is the only place that writes.

Every non-trivial outcome is published as a domain event through an
:class:`~prefact.cqrs.bus.EventBus` and, when a store is configured, appended to
an append-only :class:`~prefact.cqrs.store.EventStore` so the history can be
replayed (event sourcing).
"""

from prefact.cqrs.bus import EventBus
from prefact.cqrs.commands.refactoring import FixFile, RefactoringCommandHandler
from prefact.cqrs.events import (
    FixApplied,
    FixFailed,
    IssueDetected,
    PipelineCompleted,
    PipelineStarted,
    ScanCompleted,
    ScanStarted,
    ValidationCompleted,
)
from prefact.cqrs.queries.analysis import (
    AnalysisQueryHandler,
    CollectFiles,
    ScanPaths,
    ScanSources,
    ValidateFile,
)
from prefact.cqrs.store import EventStore, InMemoryEventStore, JsonlEventStore

__all__ = [
    "EventBus",
    "EventStore",
    "InMemoryEventStore",
    "JsonlEventStore",
    "FixFile",
    "RefactoringCommandHandler",
    "FixApplied",
    "FixFailed",
    "IssueDetected",
    "PipelineCompleted",
    "PipelineStarted",
    "ScanCompleted",
    "ScanStarted",
    "ValidationCompleted",
    "AnalysisQueryHandler",
    "CollectFiles",
    "ScanPaths",
    "ScanSources",
    "ValidateFile",
]
