"""Detect duplicate imports using importchecker."""

import ast
from pathlib import Path
from typing import List

from prefact.models import Fix, Issue, Severity, ValidationResult
from prefact.rules import BaseRule, register


@register
class ImportCheckerDuplicateImports(BaseRule):
    """Detect duplicate imports using importchecker."""

    rule_id = "importchecker-duplicate-imports"
    description = "Detect duplicate imports using importchecker library"

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        issues = []

        # Parse AST to find imports
        try:
            tree = ast.parse(source)
            import_map = {}

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name.split(".")[0]
                        if name in import_map:
                            issues.append(
                                Issue(
                                    rule_id=self.rule_id,
                                    file=path,
                                    line=node.lineno,
                                    col=node.col_offset,
                                    message=f"Duplicate import: {name}",
                                    severity=Severity.WARNING,
                                    original=name,
                                )
                            )
                        else:
                            import_map[name] = node.lineno
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        name = alias.asname or alias.name
                        if name in import_map and import_map[name] != node.lineno:
                            full_name = f"{module}.{name}" if module else name
                            issues.append(
                                Issue(
                                    rule_id=self.rule_id,
                                    file=path,
                                    line=node.lineno,
                                    col=node.col_offset,
                                    message=f"Duplicate import: {full_name}",
                                    severity=Severity.WARNING,
                                    original=full_name,
                                )
                            )
                        else:
                            import_map[name] = node.lineno
        except SyntaxError:
            pass

        return issues

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        # Use existing duplicate imports fixer
        from prefact.rules.duplicate_imports import DuplicateImports

        fixer = DuplicateImports(self.config)
        return fixer.fix(path, source, issues)

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        return self._validate_by_rescan(
            path,
            original,
            fixed,
            "no_duplicate_imports",
            "Still has {count} duplicate imports",
        )
