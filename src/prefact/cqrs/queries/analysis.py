"""Queries and handler for the ``analysis`` bounded context.

The read side of prefact's pipeline: discovering files, scanning them for
issues, and validating fixed sources. Handlers delegate to the existing
:class:`~prefact.scanner.Scanner` and :class:`~prefact.validator.Validator` and
publish ``analysis.*`` events as a side effect of the read.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from prefact.cqrs.bus import EventBus
from prefact.cqrs.events import (
    IssueDetected,
    ScanCompleted,
    ScanStarted,
    ValidationCompleted,
)
from prefact.cqrs.queries.base import Query
from prefact.models import Issue, ValidationResult
from prefact.scanner import Scanner
from prefact.validator import Validator


@dataclass(frozen=True)
class CollectFiles(Query):
    """Discover the files that match the configured include/exclude patterns."""


@dataclass(frozen=True)
class ScanSources(Query):
    """Scan preloaded sources (``path -> content``) without touching disk."""

    sources: dict[Path, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ScanPaths(Query):
    """Scan files by path, reading each one from disk."""

    paths: list[Path] = field(default_factory=list)


@dataclass(frozen=True)
class ValidateFile(Query):
    """Validate a fixed source against its original, for the affected issues."""

    path: Path
    original: str
    fixed: str
    issues: list[Issue] = field(default_factory=list)


class AnalysisQueryHandler:
    """Answers analysis queries and emits ``analysis.*`` events."""

    def __init__(self, scanner: Scanner, validator: Validator, bus: EventBus) -> None:
        self.scanner = scanner
        self.validator = validator
        self.bus = bus

    def handle(self, query: Query) -> Any:
        """Dispatch *query* to the appropriate handler."""
        if isinstance(query, CollectFiles):
            return self._collect_files(query)
        if isinstance(query, ScanSources):
            return self._scan_sources(query)
        if isinstance(query, ScanPaths):
            return self._scan_paths(query)
        if isinstance(query, ValidateFile):
            return self._validate_file(query)
        raise TypeError(f"Unknown query type: {type(query).__name__}")

    def _collect_files(self, query: CollectFiles) -> list[Path]:
        return self.scanner.collect_files()

    def _scan_sources(self, query: ScanSources) -> dict[Path, list[Issue]]:
        self.bus.publish(ScanStarted(file_count=len(query.sources)))
        results = self.scanner.scan_sources(query.sources)
        self._emit_scan_completed(len(query.sources), results)
        return results

    def _scan_paths(self, query: ScanPaths) -> dict[Path, list[Issue]]:
        self.bus.publish(ScanStarted(file_count=len(query.paths)))
        results = self.scanner.scan(query.paths)
        self._emit_scan_completed(len(query.paths), results)
        return results

    def _emit_scan_completed(
        self, file_count: int, results: dict[Path, list[Issue]]
    ) -> None:
        issue_count = 0
        for file_issues in results.values():
            for issue in file_issues:
                issue_count += 1
                self.bus.publish(
                    IssueDetected(
                        rule_id=issue.rule_id,
                        file=str(issue.file),
                        line=issue.line,
                        col=issue.col,
                        message=issue.message,
                        severity=issue.severity.value,
                    )
                )
        self.bus.publish(
            ScanCompleted(file_count=file_count, issue_count=issue_count)
        )

    def _validate_file(self, query: ValidateFile) -> list[ValidationResult]:
        results = self.validator.validate_file(
            query.path, query.original, query.fixed, query.issues
        )
        for result in results:
            self.bus.publish(
                ValidationCompleted(file=str(result.file), passed=result.passed)
            )
        return results
