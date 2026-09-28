"""Engine – orchestrates the full scan → fix → validate pipeline.

The engine keeps the imperative orchestration (file discovery, RAM preloading,
large-file splitting) and delegates the actual work to the CQRS handlers:

* reads (collect files, scan, validate) go through the ``analysis`` query
  handler;
* writes (fix) go through the ``refactoring`` command handler.

Every step is published on the shared :class:`~prefact.cqrs.bus.EventBus` and,
when an event store is configured, persisted for replay.
"""

from pathlib import Path

from prefact.config import Config
from prefact.cqrs import (
    EventBus,
    EventStore,
    FixFile,
    InMemoryEventStore,
    JsonlEventStore,
    PipelineCompleted,
    PipelineStarted,
    RefactoringCommandHandler,
)
from prefact.cqrs.queries.analysis import (
    AnalysisQueryHandler,
    CollectFiles,
    ScanPaths,
    ScanSources,
    ValidateFile,
)
from prefact.fixer import Fixer
from prefact.models import PipelineResult
from prefact.scanner import Scanner
from prefact.validator import Validator


class RefactoringEngine:
    """Main entry point: scan the project, apply fixes, validate results."""

    def __init__(
        self,
        config: Config,
        *,
        bus: EventBus | None = None,
        store: EventStore | None = None,
    ) -> None:
        self.config = config
        self.scanner = Scanner(config)
        self.fixer = Fixer(config)
        self.validator = Validator(config)

        if store is None:
            store = (
                JsonlEventStore(config.event_store)
                if config.event_store is not None
                else InMemoryEventStore()
            )
        self.store = store
        self.bus = bus if bus is not None else EventBus(store=store)
        if self.bus.store is None:
            self.bus.store = store

        self.queries = AnalysisQueryHandler(self.scanner, self.validator, self.bus)
        self.commands = RefactoringCommandHandler(self.fixer, self.bus)

    def run(self, *, dry_run: bool | None = None) -> PipelineResult:
        if dry_run is None:
            dry_run = self.config.dry_run

        pipeline_outcome = PipelineResult(dry_run=dry_run)
        self.bus.publish(PipelineStarted(dry_run=dry_run))

        # Collect all files first
        files = self.queries.handle(CollectFiles())
        if not files:
            self.bus.publish(PipelineCompleted())
            return pipeline_outcome

        # Preload small files into RAM to avoid multiple I/O operations
        sources = self._preload_sources(files)

        # Separate files that weren't preloaded (large files)
        large_files = [f for f in files if f not in sources]

        # Phase 1 – Scan (using preloaded sources for small files, direct read for large)
        issues_map = {}
        if sources:
            issues_map.update(self.queries.handle(ScanSources(sources=sources)))
        if large_files:
            issues_map.update(self.queries.handle(ScanPaths(paths=large_files)))

        for file_issues in issues_map.values():
            pipeline_outcome.issues_found.extend(file_issues)

        if not pipeline_outcome.issues_found:
            self.bus.publish(PipelineCompleted())
            return pipeline_outcome

        # Phase 2 – Fix (using preloaded sources when available)
        for path, issues in issues_map.items():
            if path in sources:
                original = sources[path]
            else:
                # Large file - read directly (always need original for validation)
                original = path.read_text(encoding="utf-8")

            fixed_source, fixes = self.commands.handle(
                FixFile(path=path, source=original, issues=issues, dry_run=dry_run)
            )
            for fix in fixes:
                (pipeline_outcome.fixes_applied if fix.applied else pipeline_outcome.fixes_failed).append(
                    fix
                )

            # Phase 3 – Validate
            validations = self.queries.handle(
                ValidateFile(path=path, original=original, fixed=fixed_source, issues=issues)
            )
            pipeline_outcome.validations.extend(validations)

        self.bus.publish(
            PipelineCompleted(
                issues_found=pipeline_outcome.total_issues,
                fixes_applied=pipeline_outcome.total_fixed,
                fixes_failed=pipeline_outcome.total_failed,
                all_valid=pipeline_outcome.all_valid,
            )
        )
        return pipeline_outcome

    def scan_only(self) -> PipelineResult:
        scan_outcome = PipelineResult(dry_run=True)

        # Collect all files first
        files = self.queries.handle(CollectFiles())
        if not files:
            return scan_outcome

        # Preload small files into RAM
        sources = self._preload_sources(files)

        # Separate files that weren't preloaded (large files)
        large_files = [f for f in files if f not in sources]

        # Scan both preloaded and large files
        issues_map = {}
        if sources:
            issues_map.update(self.queries.handle(ScanSources(sources=sources)))
        if large_files:
            issues_map.update(self.queries.handle(ScanPaths(paths=large_files)))

        for file_issues in issues_map.values():
            scan_outcome.issues_found.extend(file_issues)

        return scan_outcome

    def run_file(self, path: Path, *, dry_run: bool = False) -> PipelineResult:
        file_outcome = PipelineResult(dry_run=dry_run)

        # For single file, just load it directly
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return file_outcome

        sources = {path: source}
        issues_map = self.queries.handle(ScanSources(sources=sources))
        issues = issues_map.get(path, [])
        file_outcome.issues_found.extend(issues)

        if not issues:
            return file_outcome

        fixed_source, fixes = self.commands.handle(
            FixFile(path=path, source=source, issues=issues, dry_run=dry_run)
        )
        for fix in fixes:
            (file_outcome.fixes_applied if fix.applied else file_outcome.fixes_failed).append(fix)

        validations = self.queries.handle(
            ValidateFile(path=path, original=source, fixed=fixed_source, issues=issues)
        )
        file_outcome.validations.extend(validations)
        return file_outcome

    def _preload_sources(self, files: list[Path] | None = None) -> dict[Path, str]:
        """Preload small file sources into RAM to avoid multiple I/O operations.

        Returns a dictionary mapping file paths to their contents.
        Only loads files under 100KB to avoid excessive memory usage.

        Args:
            files: List of files to preload. If None, collects all files.
        """
        sources = {}
        max_file_size = 100 * 1024  # 100KB

        # Collect files if not provided
        if files is None:
            files = self.scanner.collect_files()

        # Load file contents into RAM
        for path in files:
            try:
                # Skip files larger than 100KB
                if path.stat().st_size > max_file_size:
                    if self.config.verbose:
                        print(
                            f"Skipping large file (>{max_file_size // 1024}KB): {path}"
                        )
                    continue

                source = path.read_text(encoding="utf-8")
                sources[path] = source
            except (OSError, UnicodeDecodeError):
                # Skip files that can't be read
                continue

        if self.config.verbose:
            total_files = len(files) if files else 0
            preloaded_count = len(sources)
            total_bytes = sum(len(s) for s in sources.values())
            print(
                f"Preloaded {preloaded_count}/{total_files} files into RAM ({total_bytes} bytes)"
            )

        return sources
