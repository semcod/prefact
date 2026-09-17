"""Domain events for the ``analysis`` bounded context (query side).

These events describe observations made while reading the codebase. They carry
only identifiers and scalar facts, never the full ``Issue``/``ValidationResult``
value objects, so they remain trivially serialisable to the event store.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from prefact.cqrs.events.base import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ScanStarted(DomainEvent):
    """A scan pass over a set of files has started."""

    name: ClassVar[str] = "analysis.scan.started"

    file_count: int = 0


@dataclass(frozen=True, kw_only=True)
class ScanCompleted(DomainEvent):
    """A scan pass has finished."""

    name: ClassVar[str] = "analysis.scan.completed"

    file_count: int = 0
    issue_count: int = 0


@dataclass(frozen=True, kw_only=True)
class IssueDetected(DomainEvent):
    """A single issue was detected during scanning."""

    name: ClassVar[str] = "analysis.issue.detected"

    rule_id: str
    file: str
    line: int
    col: int
    message: str
    severity: str


@dataclass(frozen=True, kw_only=True)
class ValidationCompleted(DomainEvent):
    """A post-fix validation check for a file has completed."""

    name: ClassVar[str] = "analysis.validation.completed"

    file: str
    passed: bool
