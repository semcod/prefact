"""Ensure import sections are properly separated by blank lines."""

from pathlib import Path
from typing import List

from prefact.config import Config
from prefact.models import Fix, Issue, Severity, ValidationResult

try:
    from prefact.rules import BaseRule, register
except ImportError:
    from .. import BaseRule, register

from .helper import HAS_ISORT, ISortHelper


@register
class ImportSectionSeparator(BaseRule):
    """Ensure import sections are properly separated."""

    rule_id = "import-section-separators"
    description = "Ensure import sections are separated by blank lines"

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.isort_config = {
            "profile": config.get_rule_option("sorted-imports", "profile", "black"),
            "known_first_party": [config.package_name or "prefact"],
        }

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        # Skip if isort is not available
        if not HAS_ISORT:
            return []
        issues = []

        # Check for missing section separators
        if ISortHelper._needs_section_separators(source, self.isort_config):
            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    file=path,
                    line=1,
                    col=0,
                    message="Import sections should be separated by blank lines",
                    severity=Severity.INFO,
                    original="imports without separators",
                )
            )

        return issues

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        if not issues or not HAS_ISORT:
            return source, []

        fixed_source = ISortHelper.fix_source(source, self.isort_config)
        fixes = []

        if fixed_source != source:
            fixes.append(
                Fix(
                    issue=issues[0],
                    file=path,
                    original_code="imports without separators",
                    fixed_code="imports with proper separators",
                    applied=True,
                )
            )

        return fixed_source, fixes

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        # Skip if isort is not available
        if not HAS_ISORT:
            return ValidationResult(file=path, passed=True, checks=[], errors=[])
        needs_separators = ISortHelper._needs_section_separators(
            fixed, self.isort_config
        )

        return ValidationResult(
            file=path,
            passed=not needs_separators,
            checks=["section_separators_present"] if not needs_separators else [],
            errors=["Missing section separators"] if needs_separators else [],
        )
