"""Optimize imports based on usage analysis."""

from pathlib import Path
from typing import Dict, List

from prefact.models import Fix, Issue, Severity, ValidationResult
from prefact.rules import BaseRule, register

from .helper import ImportCheckerHelper

PORT_3 = 3
CONSTANT_4 = 4
PORT_6 = 6


@register
class ImportOptimizer(BaseRule):
    """Optimize imports based on importchecker analysis."""

    rule_id = "import-optimization"
    description = "Optimize imports based on usage analysis"

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        issues = []

        # Get unused imports from importchecker
        unused = ImportCheckerHelper.check_file(path)

        # Get all imports
        all_imports = self._extract_all_imports(source)

        # Find imports that are used only once
        single_use = []
        for imp in all_imports:
            if not any(u["import"] == imp["name"] for u in unused):
                usage_count = self._count_usage(source, imp["name"])
                if usage_count == 1:
                    single_use.append(imp)

        # Report single-use imports
        for imp in single_use:
            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    file=path,
                    line=imp["line"],
                    col=0,
                    message=f"Import used only once: {imp['name']}",
                    severity=Severity.INFO,
                    original=imp["name"],
                )
            )

        return issues

    def _extract_all_imports(self, source: str) -> List[Dict]:
        """Extract all imports with their locations."""
        imports = []
        lines = source.splitlines()

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                if stripped.startswith("from "):
                    from_tokens = stripped.split()
                    if len(from_tokens) >= CONSTANT_4:
                        module = from_tokens[1]
                        names = from_tokens[PORT_3].split(",")
                        for name in names:
                            clean_name = name.strip().split(" as ")[0]
                            imports.append(
                                {
                                    "name": clean_name,
                                    "line": f"{i}{1}",
                                    "module": module,
                                }
                            )
                else:
                    names = stripped[PORT_6:].split(",")
                    for name in names:
                        clean_name = name.strip().split(" as ")[0].split(".")[0]
                        imports.append(
                            {"name": clean_name, "line": f"{i}{1}", "module": None}
                        )

        return imports

    def _count_usage(self, source: str, symbol: str) -> int:
        """Count how many times an import is used."""
        # Simple string-based counting
        # Real implementation would use AST for accuracy
        count = 0
        lines = source.splitlines()

        # Skip import lines
        import_lines = set()
        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ")):
                import_lines.add(i)

        # Count usage in non-import lines
        for i, line in enumerate(lines):
            if i not in import_lines:
                # Count occurrences of the import name
                count += line.count(symbol)

        return count

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        # Optimization suggestions only - no automatic fixes
        return source, []

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        return ValidationResult(
            file=path, passed=True, checks=["imports_analyzed"], errors=[]
        )
