"""Ruff-based rules - fast implementation for multiple rule types."""

import json
import subprocess
from pathlib import Path
from typing import Dict, List

from prefact.models import Fix, Issue, Severity, ValidationResult

try:
    from prefact.rules import BaseRule, register
except ImportError:
    from ..rules import BaseRule, register


class RuffHelper:
    """Helper class for Ruff operations."""

    _CACHE: Dict[str, List[Dict]] = {}

    @classmethod
    def check_file(cls, file_path: Path, select_codes: List[str]) -> List[Dict]:
        """Run Ruff on a single file and return JSON results, caching per file."""
        file_key = str(file_path)
        if file_key not in cls._CACHE:
            try:
                ruff_run = subprocess.run(
                    [
                        "ruff",
                        "check",
                        file_key,
                        "--select",
                        "F401,F811,F403,T201,I001,E,W,F,I",
                        "--output-format",
                        "json",
                        "--no-fix",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if ruff_run.stdout.strip():
                    cls._CACHE[file_key] = json.loads(ruff_run.stdout)
                else:
                    cls._CACHE[file_key] = []
            except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
                cls._CACHE[file_key] = []

        all_issues = cls._CACHE.get(file_key, [])
        codes_set = set(select_codes)
        return [
            issue
            for issue in all_issues
            if issue.get("code") in codes_set
            or any(issue.get("code", "").startswith(c) for c in codes_set)
        ]

    @staticmethod
    def fix_file(file_path: Path, select_codes: List[str]) -> bool:
        """Run Ruff with --fix on a file."""
        try:
            subprocess.run(
                [
                    "ruff",
                    "check",
                    str(file_path),
                    "--select",
                    ",".join(select_codes),
                    "--fix",
                ],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def fix_source(source: str, select_codes: List[str]) -> str:
        """Fix source code in memory using Ruff."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(source)
            tmp_path = tmp.name

        try:
            ruff_applied = RuffHelper.fix_file(Path(tmp_path), select_codes)
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

        # Ruff can remove print statements
        prints_removed = RuffHelper.fix_file(path, ["T201"])
        fixes = []

        if prints_removed:
            fixed_source = path.read_text(encoding="utf-8")
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

        # Use Ruff to remove unused imports
        unused_imports_removed = RuffHelper.fix_file(path, ["F401"])
        fixes = []

        if unused_imports_removed:
            fixed_source = path.read_text(encoding="utf-8")
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

        # Use Ruff to sort imports
        sort_applied = RuffHelper.fix_file(path, ["I001", "I002"])
        fixes = []

        if sort_applied:
            fixed_source = path.read_text(encoding="utf-8")
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
