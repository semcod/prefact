import ast
from pathlib import Path

from prefact.models import Fix, Issue, Severity, ValidationResult

try:
    from prefact.rules import BaseRule, register
except ImportError:
    from ..rules import BaseRule, register


@register
class UnusedImports(BaseRule):
    rule_id = "unused-imports"
    description = "Detect unused imports in Python files"

    def scan_file(self, path: Path, source: str) -> list[Issue]:
        issues: list[Issue] = []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return issues

        imported = _collect_imported_names(tree)
        used = _collect_used_names(tree)
        all_exports = _collect_all_exports(tree)

        for name, imp_node in imported.items():
            if name.startswith("_"):
                continue  # convention: _Foo may be re-exported
            if name in all_exports:
                continue  # exported via __all__
            if name not in used:
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        file=path,
                        line=imp_node.lineno,
                        col=imp_node.col_offset,
                        message=f"Unused import: '{name}'",
                        severity=Severity.INFO,
                        original=name,
                    )
                )
        return issues

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        checks, errors = [], []
        try:
            ast.parse(fixed)
            checks.append("syntax_valid")
        except SyntaxError as exc:
            errors.append(f"SyntaxError: {exc}")
        return ValidationResult(file=path, passed=not errors, checks=checks, errors=errors)

    def fix(self, path: Path, source: str, issues: list[Issue]) -> tuple[str, list[Fix]]:
        if not issues:
            return source, []

        unused_names = {i.original for i in issues}
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return source, []

        lines = source.splitlines(keepends=True)
        lines_to_remove: set[int] = set()
        fixes: list[Fix] = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ImportFrom):
                self.process_import_from(node, lines, lines_to_remove, fixes, issues[0], path, unused_names)
            elif isinstance(node, ast.Import):
                self.process_import(node, lines, lines_to_remove, fixes, issues[0], path, unused_names)

        new_lines = self.remove_lines(lines, lines_to_remove)
        return "".join(new_lines), fixes

    def remove_lines(self, lines: list[str], lines_to_remove: set[int]) -> list[str]:
        return [l for i, l in enumerate(lines, 1) if i not in lines_to_remove]

    def process_import_from(self, node: ast.ImportFrom, lines: list[str], lines_to_remove: set[int], fixes: list[Fix], issue: Issue, path: Path, unused_names: set[str]) -> None:
        """Process ImportFrom node and mark unused imports for removal."""
        unused_names_in_import = []
        all_unused = True

        for alias in node.names:
            name = alias.asname or alias.name
            if name in unused_names:
                unused_names_in_import.append(alias.name)
            else:
                all_unused = False

        if all_unused:
            # Remove entire import line
            lines_to_remove.add(node.lineno)
            fixes.append(Fix(
                issue=issue,
                file=path,
                original_code=lines[node.lineno - 1],
                fixed_code="",
                applied=True
            ))
        elif unused_names_in_import:
            # Remove only unused names from the import
            line_idx = node.lineno - 1
            if line_idx < len(lines):
                original_line = lines[line_idx]
                modified_line = self._remove_unused_from_line(original_line, unused_names_in_import)
                if modified_line != original_line:
                    lines[line_idx] = modified_line
                    fixes.append(Fix(
                        issue=issue,
                        file=path,
                        original_code=original_line,
                        fixed_code=modified_line,
                        applied=True
                    ))

    def process_import(self, node: ast.Import, lines: list[str], lines_to_remove: set[int], fixes: list[Fix], issue: Issue, path: Path, unused_names: set[str]) -> None:
        """Process Import node and mark unused imports for removal."""
        unused_aliases = []
        all_unused = True

        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            if name in unused_names:
                unused_aliases.append(alias.name)
            else:
                all_unused = False

        if all_unused:
            # Remove entire import line
            lines_to_remove.add(node.lineno)
            fixes.append(Fix(
                issue=issue,
                file=path,
                original_code=lines[node.lineno - 1],
                fixed_code="",
                applied=True
            ))
        elif unused_aliases:
            # Remove only unused imports from the line
            line_idx = node.lineno - 1
            if line_idx < len(lines):
                original_line = lines[line_idx]
                modified_line = self._remove_unused_from_import_line(original_line, unused_aliases)
                if modified_line != original_line:
                    lines[line_idx] = modified_line
                    fixes.append(Fix(
                        issue=issue,
                        file=path,
                        original_code=original_line,
                        fixed_code=modified_line,
                        applied=True
                    ))

    def _remove_unused_from_line(self, line: str, used_names: list[str]) -> str:
        """Remove unused names from a 'from ... import ...' line."""
        import re
        # Match the import part after 'from ... import'
        match = re.match(r'(\s*from\s+[^\s]+\s+import\s+)(.+)', line)
        if match:
            prefix = match.group(1)
            imports_part = match.group(2)
            # Filter out unused names
            imports = [imp.strip() for imp in imports_part.split(',')]
            filtered = [imp for imp in imports if any(name in imp for name in used_names)]
            if filtered:
                return prefix + ', '.join(filtered) + '\n'
            else:
                return ''  # Will be removed by line removal
        return line

    def _remove_unused_from_import_line(self, line: str, used_aliases: list[str]) -> str:
        """Remove unused imports from an 'import ...' line."""
        import re
        # Match the import part after 'import'
        match = re.match(r'(\s*import\s+)(.+)', line)
        if match:
            prefix = match.group(1)
            imports_part = match.group(2)
            # Filter out unused imports
            imports = [imp.strip() for imp in imports_part.split(',')]
            filtered = [imp for imp in imports if any(alias in imp for alias in used_aliases)]
            if filtered:
                return prefix + ', '.join(filtered) + '\n'
            else:
                return ''  # Will be removed by line removal
        return line


def _collect_imported_names(tree: ast.AST) -> dict[str, ast.AST]:
    """Collect all imported names from the AST."""
    imported = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split('.')[0]
                imported[name] = node
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                imported[name] = node
    return imported


def _collect_used_names(tree: ast.AST) -> set[str]:
    """Collect all used names in the code."""
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            # For attributes like 'module.name', collect the module part
            if isinstance(node.value, ast.Name):
                used.add(node.value.id)
    return used


def _collect_all_exports(tree: ast.AST) -> set[str]:
    """Collect names exported via __all__."""
    exports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                exports.add(elt.value)
    return exports
