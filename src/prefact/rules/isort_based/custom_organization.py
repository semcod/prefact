"""Organize imports according to custom project rules."""

from pathlib import Path
from typing import Dict, List

from prefact.config import Config
from prefact.models import Fix, Issue, Severity, ValidationResult

try:
    from prefact.rules import BaseRule, register
except ImportError:
    from .. import BaseRule, register

from .helper import HAS_ISORT, ISortHelper


@register
class CustomImportOrganization(BaseRule):
    """Organize imports according to custom rules."""

    rule_id = "custom-import-organization"
    description = "Organize imports according to custom project rules"

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.custom_rules = self._load_custom_rules()

    def _load_custom_rules(self) -> Dict:
        """Load custom import organization rules."""
        return {
            "group_by_package": self.config.get_rule_option(
                self.rule_id, "group_by_package", False
            ),
            "alphabetical_within_groups": self.config.get_rule_option(
                self.rule_id, "alphabetical_within_groups", True
            ),
            "custom_groups": self.config.get_rule_option(
                self.rule_id, "custom_groups", {}
            ),
            "required_after_imports": self.config.get_rule_option(
                self.rule_id, "required_after_imports", []
            ),
        }

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        # Skip if isort is not available
        if not HAS_ISORT:
            return []
        import ast

        issues = []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return issues

        # Find all import statements
        imports = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "line": node.lineno,
                            "type": "import",
                            "module": alias.name,
                            "name": alias.asname or alias.name,
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(
                        {
                            "line": node.lineno,
                            "type": "from",
                            "module": module,
                            "name": alias.asname or alias.name,
                            "level": node.level,
                        }
                    )

        # Check organization
        if self.custom_rules["group_by_package"]:
            issues.extend(self._check_grouping(path, imports))

        if self.custom_rules["alphabetical_within_groups"]:
            issues.extend(self._check_alphabetical(path, imports))

        return issues

    def _check_grouping(self, path: Path, imports: List[Dict]) -> List[Issue]:
        """Check if imports are properly grouped by package."""
        issues = []
        current_package = None

        for imp in imports:
            package = imp["module"].split(".")[0] if imp["module"] else ""

            if current_package and package != current_package:
                # Check if there's a blank line between packages
                # This is simplified - real implementation would check source
                pass

            current_package = package

        return issues

    def _check_alphabetical(self, path: Path, imports: List[Dict]) -> List[Issue]:
        """Check if imports are alphabetical within groups."""
        issues = []

        # Group by module
        groups = {}
        for imp in imports:
            module = imp["module"]
            if module not in groups:
                groups[module] = []
            groups[module].append(imp)

        # Check alphabetical order within each group
        for module, group in groups.items():
            names = [imp["name"] for imp in group]
            if names != sorted(names):
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        file=path,
                        line=group[0]["line"],
                        col=0,
                        message=f"Imports from '{module}' not in alphabetical order",
                        severity=Severity.INFO,
                        original="unalphabetical imports",
                    )
                )

        return issues

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        # Use ISort with custom configuration
        custom_config = {
            "profile": "black",
            "force_single_line": self.custom_rules["group_by_package"],
            "sort_order": "natural"
            if self.custom_rules["alphabetical_within_groups"]
            else "native",
        }

        fixed_source = ISortHelper.fix_source(source, custom_config)
        fixes = []

        if fixed_source != source:
            for issue in issues:
                fixes.append(
                    Fix(
                        issue=issue,
                        file=path,
                        original_code=issue.original,
                        fixed_code="organized imports",
                        applied=True,
                    )
                )

        return fixed_source, fixes

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        # Skip if isort is not available
        if not HAS_ISORT:
            return ValidationResult(file=path, passed=True, checks=[], errors=[])
        # Re-scan to check if organization is correct
        issues = self.scan_file(path, fixed)

        return ValidationResult(
            file=path,
            passed=len(issues) == 0,
            checks=["imports_organized"] if not issues else [],
            errors=[f"Still has {len(issues)} organization issues"] if issues else [],
        )
