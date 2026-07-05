"""Sort imports using ISort."""

from pathlib import Path
from typing import Dict, List

from prefact.config import Config
from prefact.config_extended import DEFAULT_MAX_LINE_LENGTH
from prefact.models import Fix, Issue, Severity, ValidationResult

try:
    from prefact.rules import BaseRule, register
except ImportError:
    from .. import BaseRule, register

from .helper import HAS_ISORT, ISortHelper


@register
class ISortedImports(BaseRule):
    """Sort imports using ISort."""

    rule_id = "sorted-imports"
    description = "Sort imports according to PEP8 using ISort"

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.isort_config = self._load_isort_config()

    def _load_isort_config(self) -> Dict:
        """Load ISort configuration from prefact config."""
        config = {
            "profile": self.config.get_rule_option(self.rule_id, "profile", "black"),
            "line_length": self.config.get_rule_option(
                self.rule_id, "line_length", DEFAULT_MAX_LINE_LENGTH
            ),
            "known_first_party": self.config.get_rule_option(
                self.rule_id,
                "known_first_party",
                [self.config.package_name or "prefact"],
            ),
            "sections": self.config.get_rule_option(
                self.rule_id,
                "sections",
                ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"],
            ),
        }

        # Add custom settings
        custom_settings = self.config.get_rule_option(
            self.rule_id, "custom_settings", {}
        )
        config.update(custom_settings)

        return config

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        # Skip if isort is not available
        if not HAS_ISORT:
            return []

        issues = []
        results = ISortHelper.check_source(source, self.isort_config)

        for item in results:
            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    file=path,
                    line=item.get("line", 1),
                    col=0,
                    message=item.get("message", "Imports not sorted"),
                    severity=Severity.INFO,
                    original="unsorted imports",
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

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        # Skip if isort is not available
        if not HAS_ISORT:
            return ValidationResult(file=path, passed=True, checks=[], errors=[])
        # Verify imports are sorted
        remaining_issues = ISortHelper.check_source(fixed, self.isort_config)

        return ValidationResult(
            file=path,
            passed=len(remaining_issues) == 0,
            checks=["imports_sorted"] if not remaining_issues else [],
            errors=[f"Still has {len(remaining_issues)} sorting issues"]
            if remaining_issues
            else [],
        )
