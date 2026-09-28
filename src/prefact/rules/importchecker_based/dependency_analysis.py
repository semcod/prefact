"""Analyze import dependencies and circular imports using importchecker."""

from pathlib import Path
from typing import Dict, List

from prefact.config import Config
from prefact.models import Fix, Issue, Severity, ValidationResult
from prefact.rules import BaseRule, register

from .helper import ImportCheckerHelper

CONSTANT_4 = 4
MAX_5 = 5


@register
class ImportDependencyAnalysis(BaseRule):
    """Analyze import dependencies using importchecker."""

    rule_id = "import-dependencies"
    description = "Analyze import dependencies and circular imports"

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.checker_config = self._load_checker_config()

    def _load_checker_config(self) -> Dict:
        """Load configuration."""
        return {
            "max_depth": self.config.get_rule_option(self.rule_id, "max_depth", MAX_5),
            "detect_cycles": self.config.get_rule_option(
                self.rule_id, "detect_cycles", True
            ),
        }

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        issues = []

        # Parse imports
        imports = self._extract_imports(source)

        # Check for circular imports
        if self.checker_config["detect_cycles"]:
            circular = self._detect_circular_imports(path, imports)
            for cycle in circular:
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        file=path,
                        line=1,
                        col=0,
                        message=f"Circular import detected: {' -> '.join(cycle)}",
                        severity=Severity.ERROR,
                        original=" -> ".join(cycle),
                    )
                )

        # Check import depth
        for imp in imports:
            if imp["name"].count(".") > self.checker_config["max_depth"]:
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        file=path,
                        line=imp["line"],
                        col=0,
                        message=f"Deep import: {imp['name']} (depth: {imp['name'].count('.')})",
                        severity=Severity.WARNING,
                        original=imp["name"],
                    )
                )

        return issues

    def _extract_imports(self, source: str) -> List[Dict]:
        """Extract all imports from source."""
        imports = []
        lines = source.splitlines()

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                if stripped.startswith("from "):
                    statement_tokens = stripped.split()
                    if len(statement_tokens) >= CONSTANT_4:
                        module = statement_tokens[1]
                        imports.append({"name": module, "line": i + 1, "type": "from"})
                else:
                    statement_tokens = stripped.split()
                    if len(statement_tokens) >= 2:
                        module = statement_tokens[1].split(".")[0]
                        imports.append(
                            {"name": module, "line": i + 1, "type": "import"}
                        )

        return imports

    def _detect_circular_imports(
        self, path: Path, imports: List[Dict]
    ) -> List[List[str]]:
        """Detect circular imports (simplified implementation)."""
        # This is a simplified version - real implementation would need
        # to build a full dependency graph
        circular = []

        # Get current module name
        current_module = ImportCheckerHelper._get_module_name(path)
        if not current_module:
            return circular

        # Check if any import could be circular
        for imp in imports:
            if imp["type"] == "from":
                # Simplified check - just warn about same package imports
                if current_module.split(".")[0] in imp["name"]:
                    circular.append([current_module, imp["name"], current_module])

        return circular

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        # Import dependency issues usually require manual fixes
        return source, []

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        # Re-run analysis
        issues = self.scan_file(path, fixed)

        return ValidationResult(
            file=path,
            passed=len(issues) == 0,
            checks=["no_circular_imports", "import_depth_ok"] if not issues else [],
            errors=[issue.message for issue in issues] if issues else [],
        )
