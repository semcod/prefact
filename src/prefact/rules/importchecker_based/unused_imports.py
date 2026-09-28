"""Detect unused imports using importchecker."""

from pathlib import Path
from typing import Dict, List

from prefact.config import Config
from prefact.models import Fix, Issue, Severity, ValidationResult
from prefact.rules import BaseRule, register

from .helper import ImportCheckerHelper

PORT_3 = 3
CONSTANT_4 = 4
PORT_6 = 6


@register
class ImportCheckerUnusedImports(BaseRule):
    """Detect unused imports using importchecker."""

    rule_id = "importchecker-unused-imports"
    description = "Detect unused imports using importchecker library"

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.checker_config = self._load_checker_config()

    def _load_checker_config(self) -> Dict:
        """Load importchecker configuration."""
        return {
            "ignore_init_module": self.config.get_rule_option(
                self.rule_id, "ignore_init_module", True
            ),
            "ignore_dunder_main": self.config.get_rule_option(
                self.rule_id, "ignore_dunder_main", True
            ),
        }

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        issues = []

        # Skip if configured to ignore
        if self.checker_config["ignore_init_module"] and path.name == "__init__.py":
            return issues

        results = ImportCheckerHelper.check_file(path)

        # Map results to line numbers
        import_lines = self._find_import_lines(source)

        for item in results:
            reported_import = item.get("import", "unknown")
            line_num = import_lines.get(reported_import, 1)

            # Skip __main__ if configured
            if (
                self.checker_config["ignore_dunder_main"]
                and reported_import == "__main__"
            ):
                continue

            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    file=path,
                    line=line_num,
                    col=0,
                    message=f"Unused import: {reported_import}",
                    severity=Severity.INFO,
                    original=reported_import,
                )
            )

        return issues

    def _find_import_lines(self, source: str) -> Dict[str, int]:
        """Find line numbers for each import."""
        import_lines = {}
        lines = source.splitlines()

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                # Extract import names
                if stripped.startswith("from "):
                    from_tokens = stripped.split()
                    if len(from_tokens) >= CONSTANT_4:
                        module = from_tokens[1]
                        imports = from_tokens[PORT_3].split(",")
                        for imp in imports:
                            name = imp.strip().split(" as ")[0]
                            import_lines[name] = str(i + 1)
                            if module:
                                import_lines[f"{module}.{name}"] = str(i + 1)
                else:
                    imports = stripped[PORT_6:].split(",")  # Remove "import"
                    for imp in imports:
                        name = imp.strip().split(" as ")[0].split(".")[0]
                        import_lines[name] = str(i + 1)

        return import_lines

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        # Use existing unused imports fixer
        from prefact.rules.unused_imports import UnusedImports

        fixer = UnusedImports(self.config)
        return fixer.fix(path, source, issues)

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        # Check if unused imports remain
        results = ImportCheckerHelper.check_file(path)

        return ValidationResult(
            file=path,
            passed=len(results) == 0,
            checks=["no_unused_imports"] if not results else [],
            errors=[f"Still has {len(results)} unused imports"] if results else [],
        )
