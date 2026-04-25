"""Autoflake-based unused import and variable removal for prefact.

This module provides integration with Autoflake for removing unused imports,
unused variables, and duplicate keys.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from prefact.config import Config
from prefact.models import Fix, Issue, Severity, ValidationResult

try:
    from prefact.rules import BaseRule, register
except ImportError:
    from ..rules import BaseRule, register


def build_autoflake_check_command(file_path: Path, config: Optional[Dict] = None) -> List[str]:
    """Build the autoflake command for checking a file."""
    cmd = [
        "autoflake",
        "--check-diff",
        "--remove-unused-variables",
        "--remove-all-unused-imports",
        str(file_path)
    ]

    if config and config.get("ignore_init_module_imports"):
        cmd.append("--ignore-init-module-imports")

    return cmd


def parse_autoflake_output(output_lines: List[str]) -> List[Dict]:
    """Parse autoflake output to extract issues."""
    issues = []
    for line in output_lines:
        if line.startswith("-") and ("import" in line or "from" in line):
            # This is a removed import
            issues.append({
                "type": "unused_import",
                "line": line,
                "message": "Unused import detected"
            })
        elif line.startswith("-") and "=" in line:
            # This might be an unused variable
            issues.append({
                "type": "unused_variable",
                "line": line,
                "message": "Unused variable detected"
            })
    return issues


def run_autoflake_command(cmd: List[str]) -> subprocess.CompletedProcess:
    """Run the autoflake command and return the result."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False  # Autoflake returns non-zero on changes
    )


def create_temp_file_with_source(source: str) -> str:
    """Create a temporary file with the given source code."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
    tmp.write(source)
    tmp_path = tmp.name
    tmp.close()
    return tmp_path


def build_autoflake_fix_command(file_path: Path, config: Optional[Dict] = None) -> List[str]:
    """Build the autoflake command for fixing a file."""
    cmd = [
        "autoflake",
        "--in-place",
        "--remove-unused-variables",
        "--remove-all-unused-imports",
        str(file_path)
    ]

    if config:
        if config.get("ignore_init_module_imports"):
            cmd.append("--ignore-init-module-imports")
        if config.get("remove_duplicate_keys"):
            cmd.append("--remove-duplicate-keys")
        if config.get("remove_rhs_for_unused_variables"):
            cmd.append("--remove-rhs-for-unused-variables")

    return cmd


def create_issues_from_results(results: List[Dict], path: Path, rule_id: str) -> List[Issue]:
    """Create Issue objects from autoflake results."""
    issues = []
    line_num = 1
    for item in results:
        if item["type"] == "unused_import":
            # Extract import name from the line
            import_name = extract_import_name(item["line"])

            issues.append(Issue(
                rule_id=rule_id,
                file=path,
                line=line_num,
                col=0,
                message=f"Unused import: {import_name}",
                severity=Severity.INFO,
                original=import_name
            ))
        line_num += 1
    return issues


def extract_import_name(line: str) -> str:
    """Extract the import name from a diff line."""
    # Remove the leading "- " from diff output
    clean_line = line[2:] if line.startswith("- ") else line

    if "import " in clean_line:
        if clean_line.startswith("from "):
            # from x import y
            parts = clean_line.split()
            if len(parts) >= 4:
                return parts[3]
        else:
            # import x
            parts = clean_line.split()
            if len(parts) >= 2:
                return parts[1].split(",")[0]

    return "unknown"


def create_fixes_from_issues(issues: List[Issue], path: Path) -> List[Fix]:
    """Create Fix objects from issues."""
    fixes = []
    for issue in issues:
        fixes.append(Fix(
            issue=issue,
            file=path,
            original_code=issue.original,
            fixed_code="",
            applied=True
        ))
    return fixes


def validate_unused_imports(fixed: str, autoflake_config: Dict, path: Path) -> ValidationResult:
    """Validate that no unused imports remain."""
    remaining = AutoflakeHelper.check_source(fixed, autoflake_config)
    unused_imports = [r for r in remaining if r["type"] == "unused_import"]

    return ValidationResult(
        file=path,
        passed=len(unused_imports) == 0,
        checks=["no_unused_imports"] if not unused_imports else [],
        errors=[f"Still has {len(unused_imports)} unused imports"] if unused_imports else []
    )


class AutoflakeHelper:
    """Helper class for Autoflake operations."""

    @staticmethod
    def check_file(file_path: Path, config: Optional[Dict] = None) -> List[Dict]:
        """Check a file for unused imports and variables using Autoflake."""
        # Autoflake doesn't have a check-only mode, so we simulate it
        # by running with --check-diff flag
        cmd = build_autoflake_check_command(file_path, config)

        try:
            result = run_autoflake_command(cmd)

            # Parse output to find issues
            issues = []
            if result.returncode != 0:
                lines = result.stdout.splitlines()
                issues = parse_autoflake_output(lines)

            return issues
        except (subprocess.SubprocessError, FileNotFoundError):
            return []

    @staticmethod
    def check_source(source: str, config: Optional[Dict] = None) -> List[Dict]:
        """Check source code for unused imports and variables."""
        tmp_path = create_temp_file_with_source(source)

        try:
            return AutoflakeHelper.check_file(Path(tmp_path), config)
        finally:
            os.unlink(tmp_path)

    @staticmethod
    def fix_file(file_path: Path, config: Optional[Dict] = None) -> bool:
        """Remove unused imports and variables from a file."""
        cmd = build_autoflake_fix_command(file_path, config)

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def fix_source(source: str, config: Optional[Dict] = None) -> str:
        """Remove unused imports and variables from source code."""
        tmp_path = create_temp_file_with_source(source)

        try:
            success = AutoflakeHelper.fix_file(Path(tmp_path), config)
            if success:
                with open(tmp_path) as f:
                    return f.read()
            return source
        finally:
            os.unlink(tmp_path)


@register
class AutoflakeUnusedImports(BaseRule):
    """Remove unused imports using Autoflake."""

    rule_id = "unused-imports"
    description = "Remove unused imports using Autoflake"

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.autoflake_config = self._load_autoflake_config()

    def _load_autoflake_config(self) -> Dict:
        """Load Autoflake configuration from prefact config."""
        return {
            "ignore_init_module_imports": self.config.get_rule_option(
                self.rule_id, "ignore_init_module_imports", True
            ),
            "remove_duplicate_keys": self.config.get_rule_option(
                self.rule_id, "remove_duplicate_keys", False
            ),
        }

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        results = AutoflakeHelper.check_source(source, self.autoflake_config)
        return create_issues_from_results(results, path, self.rule_id)

    def fix(self, path: Path, source: str, issues: List[Issue]) -> tuple[str, List[Fix]]:
        if not issues:
            return source, []

        fixed_source = AutoflakeHelper.fix_source(source, self.autoflake_config)
        fixes = []

        if fixed_source != source:
            fixes = create_fixes_from_issues(issues, path)

        return fixed_source, fixes

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        return validate_unused_imports(fixed, self.autoflake_config, path)


@register
class AutoflakeUnusedVariables(BaseRule):
    """Remove unused variables using Autoflake."""

    rule_id = "unused-variables"
    description = "Remove unused variables using Autoflake"

    def __init__(self, config: Config) -> None:
        super().__init__(config)
