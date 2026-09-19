"""Domain event registry and serialisation helpers."""

from __future__ import annotations

from typing import Any

from prefact.cqrs.events.analysis import (
    IssueDetected,
    ScanCompleted,
    ScanStarted,
    ValidationCompleted,
)
from prefact.cqrs.events.base import DomainEvent
from prefact.cqrs.events.refactoring import (
    FixApplied,
    FixFailed,
    PipelineCompleted,
    PipelineStarted,
)

EVENT_TYPES: dict[str, type[DomainEvent]] = {
    cls.name: cls
    for cls in (
        ScanStarted,
        ScanCompleted,
        IssueDetected,
        ValidationCompleted,
        PipelineStarted,
        PipelineCompleted,
        FixApplied,
        FixFailed,
    )
}


def from_dict(data: dict[str, Any]) -> DomainEvent:
    """Rebuild a domain event from a serialised dictionary.

    ``data`` must contain a ``name`` key matching one of the registered event
    types. Every other key is passed as a constructor keyword argument.
    """
    event_type = EVENT_TYPES[data["name"]]
    kwargs = {k: v for k, v in data.items() if k != "name"}
    return event_type(**kwargs)


__all__ = [
    "DomainEvent",
    "EVENT_TYPES",
    "from_dict",
    "ScanStarted",
    "ScanCompleted",
    "IssueDetected",
    "ValidationCompleted",
    "PipelineStarted",
    "PipelineCompleted",
    "FixApplied",
    "FixFailed",
]
