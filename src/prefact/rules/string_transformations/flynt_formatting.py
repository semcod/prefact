"""Flynt-based string formatting optimization (alternative to StringConcatToFString)."""

import ast
from pathlib import Path
from typing import List

from prefact.models import Fix, Issue, Severity, ValidationResult

try:
    from prefact.rules import BaseRule, register
except ImportError:
    from .. import BaseRule, register

MAX_LINE_LENGTH = 88


class FlyntHelper:
    """Helper for using flynt library for string formatting."""

    @staticmethod
    def fix_source(source: str) -> str:
        """Use flynt to fix string formatting."""
        try:
            import flynt
            from flynt.api import api

            # Configure flynt
            options = {
                "aggressive": True,
                "multiline": True,
                "len_limit": MAX_LINE_LENGTH,
            }

            # Apply transformations
            result = api.fstringify(source, **options)
            return result
        except ImportError:
            # flynt not available
            return source
        except Exception:
            # Error during transformation
            return source


@register
class FlyntStringFormatting(BaseRule):
    """Use flynt library for string formatting optimizations."""

    rule_id = "string-formatting"
    description = "Optimize string formatting using flynt"

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        # For simplicity, we'll just scan for common patterns
        # that flynt can optimize
        issues = []

        # Look for .format() calls
        if ".format(" in source:
            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    file=path,
                    line=1,
                    col=0,
                    message="String .format() calls can be converted to f-strings",
                    severity=Severity.INFO,
                    original=".format()",
                )
            )

        # Look for % formatting
        if "%" in source and ("'" in source or '"' in source):
            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    file=path,
                    line=1,
                    col=0,
                    message="Old-style string formatting can be converted to f-strings",
                    severity=Severity.INFO,
                    original="% formatting",
                )
            )

        return issues

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        if not issues:
            return source, []

        fixed_source = FlyntHelper.fix_source(source)
        fixes = []

        if fixed_source != source:
            for issue in issues:
                fixes.append(
                    Fix(
                        issue=issue,
                        file=path,
                        original_code=issue.original,
                        fixed_code="f-string",
                        applied=True,
                    )
                )

        return fixed_source, fixes

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        # Simple validation - just check syntax
        try:
            ast.parse(fixed)
            return ValidationResult(
                file=path, passed=True, checks=["syntax_valid"], errors=[]
            )
        except SyntaxError as e:
            return ValidationResult(
                file=path, passed=False, checks=[], errors=[f"Syntax error: {e}"]
            )
