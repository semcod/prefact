"""Ruff-based rules - fast implementation for multiple rule types."""

import json
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from prefact.models import Fix, Issue, Severity, ValidationResult

try:
    from prefact.rules import BaseRule, register
except ImportError:
    from ..rules import BaseRule, register


class RuffHelper:
    """Helper class for Ruff operations."""

    _CACHE: Dict[str, List[Dict]] = {}
    _RUFF_AVAILABLE: Optional[bool] = None
    _LOCK = threading.Lock()

    @classmethod
    def is_available(cls) -> bool:
        """Check if ruff binary is available in PATH."""
        if cls._RUFF_AVAILABLE is None:
            cls._RUFF_AVAILABLE = shutil.which("ruff") is not None
        return cls._RUFF_AVAILABLE

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached Ruff results."""
        with cls._LOCK:
            cls._CACHE.clear()

    @classmethod
    def preload_files(cls, file_paths: Sequence[Path]) -> None:
        """Run Ruff in batch on multiple files to populate the cache."""
        if not cls.is_available():
            return

        with cls._LOCK:
            to_scan: List[Path] = []
            for fp in file_paths:
                k1 = str(fp)
                try:
                    k2 = str(fp.resolve())
                except Exception:
                    k2 = k1
                if k1 not in cls._CACHE and k2 not in cls._CACHE:
                    to_scan.append(fp)

        if not to_scan:
            return

        chunk_size = 200
        for i in range(0, len(to_scan), chunk_size):
            chunk = to_scan[i : i + chunk_size]
            batch_results: Dict[str, List[Dict]] = {}
            for p in chunk:
                batch_results[str(p)] = []
                try:
                    batch_results[str(p.resolve())] = []
                except Exception:
                    pass

            cmd = [
                "ruff",
                "check",
                "--no-cache",
                *[str(p) for p in chunk],
                "--select",
                "F401,F811,F403,T201,I001,E,W,F,I",
                "--output-format",
                "json",
                "--no-fix",
            ]
            try:
                ruff_run = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if ruff_run.stdout.strip():
                    raw_issues = json.loads(ruff_run.stdout)
                    for item in raw_issues:
                        fname = item.get("filename")
                        if fname:
                            f_path = Path(fname)
                            k1 = str(f_path)
                            try:
                                k2 = str(f_path.resolve())
                            except Exception:
                                k2 = k1
                            if k1 in batch_results:
                                batch_results[k1].append(item)
                            else:
                                batch_results[k1] = [item]
                            if k2 in batch_results and k2 != k1:
                                batch_results[k2].append(item)
                            elif k2 != k1:
                                batch_results[k2] = [item]
            except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
                pass

            with cls._LOCK:
                cls._CACHE.update(batch_results)

    @classmethod
    def check_file(cls, file_path: Path, select_codes: List[str]) -> List[Dict]:
        """Run Ruff on a single file and return JSON results, caching per file."""
        if not cls.is_available():
            return []

        file_key = str(file_path)
        try:
            resolved_key = str(file_path.resolve())
        except Exception:
            resolved_key = file_key

        if file_key not in cls._CACHE and resolved_key not in cls._CACHE:
            cls.preload_files([file_path])

        all_issues = cls._CACHE.get(file_key)
        if all_issues is None:
            all_issues = cls._CACHE.get(resolved_key, [])

        codes_set = set(select_codes)
        return [
            issue
            for issue in all_issues
            if issue.get("code") in codes_set
            or any(issue.get("code", "").startswith(c) for c in codes_set)
        ]

    @classmethod
    def fix_file(cls, file_path: Path, select_codes: List[str]) -> bool:
        """Run Ruff with --fix on a file."""
        if not cls.is_available():
            return False
        try:
            subprocess.run(
                [
                    "ruff",
                    "check",
                    "--no-cache",
                    str(file_path),
                    "--select",
                    ",".join(select_codes),
                    "--fix",
                ],
                check=True,
                capture_output=True,
            )
            with cls._LOCK:
                cls._CACHE.pop(str(file_path), None)
                try:
                    cls._CACHE.pop(str(file_path.resolve()), None)
                except Exception:
                    pass
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @classmethod
    def fix_source(cls, source: str, select_codes: List[str]) -> str:
        """Fix source code in memory using Ruff."""
        if not cls.is_available():
            return source
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(source)
            tmp_path = tmp.name

        try:
            ruff_applied = cls.fix_file(Path(tmp_path), select_codes)
            if ruff_applied:
                with open(tmp_path) as f:
                    return f.read()
            return source
        finally:
            import os

            os.unlink(tmp_path)



@register
class RuffWildcardImports(BaseRule):
    """Wildcard imports detection using Ruff."""

    rule_id = "ruff-wildcard-imports"
    description = "Detect wildcard imports (from x import *)"

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        issues = []
        results = RuffHelper.check_file(path, ["F403"])  # F403 = star-imports

        for item in results:
            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    file=path,
                    line=item["location"]["row"],
                    col=item["location"]["column"],
                    message=item["message"],
                    severity=Severity.WARNING,
                    original=item["message"],
                )
            )

        return issues

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        # Ruff doesn't auto-fix wildcard imports, so we just report
        return source, []

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        return ValidationResult(file=path, passed=True, checks=[], errors=[])


@register
class RuffPrintStatements(BaseRule):
    """Print statements detection using Ruff."""

    rule_id = "ruff-print-statements"
    description = "Detect print statements"

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        issues = []
        results = RuffHelper.check_file(path, ["T201"])  # T201 = print

        for item in results:
            # Check if file should be ignored
            if self._should_ignore_file(path):
                continue

            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    file=path,
                    line=item["location"]["row"],
                    col=item["location"]["column"],
                    message=item["message"],
                    severity=Severity.INFO,
                    original="print()",
                )
            )

        return issues

    def _should_ignore_file(self, path: Path) -> bool:
        """Check if file should be ignored based on config."""
        ignore_patterns = getattr(self.config, "ignore_print_patterns", [])
        return any(pattern in str(path) for pattern in ignore_patterns)

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        if not issues:
            return source, []

        fixed_source = RuffHelper.fix_source(source, ["T201"])
        fixes = []

        if fixed_source != source:
            for issue in issues:
                fixes.append(
                    Fix(
                        issue=issue,
                        file=path,
                        original_code="print(...)",
                        fixed_code="# Removed print statement",
                        applied=True,
                    )
                )
            return fixed_source, fixes

        return source, []

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        return ValidationResult(file=path, passed=True, checks=[], errors=[])


@register
class RuffUnusedImports(BaseRule):
    """Unused imports detection and removal using Ruff."""

    rule_id = "ruff-unused-imports"
    description = "Detect and remove unused imports"

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        issues = []
        results = RuffHelper.check_file(path, ["F401"])  # F401 = unused-import

        for item in results:
            # Extract import name from message
            diagnostic_message = item["message"]
            if "`" in diagnostic_message:
                flagged_import = diagnostic_message.split("`")[1]
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        file=path,
                        line=item["location"]["row"],
                        col=item["location"]["column"],
                        message=f"Unused import: {flagged_import}",
                        severity=Severity.INFO,
                        original=flagged_import,
                    )
                )

        return issues

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        if not issues:
            return source, []

        fixed_source = RuffHelper.fix_source(source, ["F401"])
        fixes = []

        if fixed_source != source:
            for issue in issues:
                fixes.append(
                    Fix(
                        issue=issue,
                        file=path,
                        original_code=issue.original,
                        fixed_code="",
                        applied=True,
                    )
                )
            return fixed_source, fixes

        return source, []

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        # Verify no unused imports remain
        remaining = RuffHelper.check_file(path, ["F401"])
        return ValidationResult(
            file=path,
            passed=len(remaining) == 0,
            checks=["no_unused_imports"] if not remaining else [],
            errors=[f"Still has unused imports: {len(remaining)}"] if remaining else [],
        )


@register
class RuffSortedImports(BaseRule):
    """Import sorting using Ruff."""

    rule_id = "ruff-sorted-imports"
    description = "Sort imports according to PEP8"

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        issues = []
        results = RuffHelper.check_file(
            path, ["I001", "I002"]
        )  # I001 = unsorted, I002 = missing newline

        for item in results:
            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    file=path,
                    line=item["location"]["row"],
                    col=item["location"]["column"],
                    message=item["message"],
                    severity=Severity.INFO,
                    original="unsorted imports",
                )
            )

        return issues

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        if not issues:
            return source, []

        fixed_source = RuffHelper.fix_source(source, ["I001", "I002"])
        fixes = []

        if fixed_source != source:
            for issue in issues:
                fixes.append(
                    Fix(
                        issue=issue,
                        file=path,
                        original_code="unsorted imports",
                        fixed_code="sorted imports",
                        applied=True,
                    )
                )
            return fixed_source, fixes

        return source, []

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        # Verify imports are sorted
        remaining = RuffHelper.check_file(path, ["I001", "I002"])
        return ValidationResult(
            file=path,
            passed=len(remaining) == 0,
            checks=["imports_sorted"] if not remaining else [],
            errors=["Imports not properly sorted"] if remaining else [],
        )


@register
class RuffDuplicateImports(BaseRule):
    """Duplicate imports detection using Ruff."""

    rule_id = "ruff-duplicate-imports"
    description = "Detect duplicate imports"

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        issues = []
        # Ruff doesn't have a specific code for duplicate imports
        # We'll use F811 (redefined) which catches some cases
        results = RuffHelper.check_file(path, ["F811"])

        for item in results:
            if (
                "redefined" in item["message"].lower()
                and "import" in item["message"].lower()
            ):
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        file=path,
                        line=item["location"]["row"],
                        col=item["location"]["column"],
                        message=item["message"],
                        severity=Severity.WARNING,
                        original="duplicate import",
                    )
                )

        return issues

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        # Ruff doesn't auto-fix duplicate imports
        # Would need custom implementation
        return source, []

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        return ValidationResult(file=path, passed=True, checks=[], errors=[])
