"""Domain events for the ``refactoring`` bounded context (command side).

These events describe mutations applied (or attempted) on the codebase, plus
the pipeline-level lifecycle events that frame a whole run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from prefact.cqrs.events.base import DomainEvent


@dataclass(frozen=True, kw_only=True)
class PipelineStarted(DomainEvent):
    """The scan → fix → validate pipeline has started."""

    name: ClassVar[str] = "refactoring.pipeline.started"

    dry_run: bool = False


@dataclass(frozen=True, kw_only=True)
class PipelineCompleted(DomainEvent):
    """The scan → fix → validate pipeline has completed."""

    name: ClassVar[str] = "refactoring.pipeline.completed"

    issues_found: int = 0
    fixes_applied: int = 0
    fixes_failed: int = 0
    all_valid: bool = True


@dataclass(frozen=True, kw_only=True)
class FixApplied(DomainEvent):
    """A fix was successfully applied to a file."""

    name: ClassVar[str] = "refactoring.fix.applied"

    rule_id: str
    file: str


@dataclass(frozen=True, kw_only=True)
class FixFailed(DomainEvent):
    """A fix failed to apply."""

    name: ClassVar[str] = "refactoring.fix.failed"

    rule_id: str
    file: str
    error: str = ""
