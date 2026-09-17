"""Commands and handler for the ``refactoring`` bounded context.

The write side of prefact's pipeline is expressed as ``FixFile`` commands
handled by :class:`RefactoringCommandHandler`, which delegates the actual
mutation to the existing :class:`~prefact.fixer.Fixer` and publishes a domain
event for every applied or failed fix.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from prefact.cqrs.bus import EventBus
from prefact.cqrs.commands.base import Command
from prefact.cqrs.events import FixApplied, FixFailed
from prefact.fixer import Fixer
from prefact.models import Fix, Issue


@dataclass(frozen=True)
class FixFile(Command):
    """Intent to fix the issues of a single file."""

    path: Path
    source: str
    issues: list[Issue] = field(default_factory=list)
    dry_run: bool = False


class RefactoringCommandHandler:
    """Applies refactoring commands and emits fix events."""

    def __init__(self, fixer: Fixer, bus: EventBus) -> None:
        self.fixer = fixer
        self.bus = bus

    def handle(self, command: Command) -> tuple[str, list[Fix]]:
        """Dispatch *command* to the appropriate handler."""
        if isinstance(command, FixFile):
            return self._fix_file(command)
        raise TypeError(f"Unknown command type: {type(command).__name__}")

    def _fix_file(self, command: FixFile) -> tuple[str, list[Fix]]:
        fixed_source, fixes = self.fixer.fix_file_with_source(
            command.path, command.source, command.issues, dry_run=command.dry_run
        )
        for fix in fixes:
            if fix.applied:
                self.bus.publish(
                    FixApplied(rule_id=fix.issue.rule_id, file=str(fix.file))
                )
            else:
                self.bus.publish(
                    FixFailed(
                        rule_id=fix.issue.rule_id,
                        file=str(fix.file),
                        error=fix.error or "",
                    )
                )
        return fixed_source, fixes
