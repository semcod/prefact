"""LibCST-based string concatenation to f-string transformation."""

import ast
from pathlib import Path
from typing import Any, List, Optional

import libcst as cst

from prefact.models import Fix, Issue, Severity, ValidationResult

try:
    from prefact.rules import BaseRule, register
except ImportError:
    from .. import BaseRule, register


class StringConcatTransformer(cst.CSTTransformer):
    """Transform string concatenations to f-strings."""

    def __init__(self) -> None:
        self.fixes = []
        self.changes = []

    def _get_line_number(self, node: cst.CSTNode) -> int:
        """Get line number from CST node metadata."""
        if hasattr(node, "position") and node.position:
            return node.position.start.line
        # Try to get from the first child if position is not available
        for child in node.children:
            if hasattr(child, "position") and child.position:
                return child.position.start.line
        return 0

    def leave_BinaryOperation(
        self,
        original_node: cst.BinaryOperation,
        updated_node: cst.BinaryOperation,
    ) -> cst.CSTNode:
        # Check if this is a string concatenation
        if not isinstance(updated_node.operator, cst.Add):
            return updated_node

        # Collect all string parts
        parts = self._collect_string_parts(updated_node)

        if parts and self._should_transform(parts):
            # Create f-string
            fstring = self._create_fstring(parts)
            if fstring:
                self.fixes.append(
                    {
                        "line": self._get_line_number(original_node),
                        "original": cst.Module([]).code_for_node(original_node),
                        "fixed": cst.Module([]).code_for_node(fstring),
                    }
                )
                return fstring

        return updated_node

    def _collect_string_parts(self, node: cst.BinaryOperation) -> List[dict]:
        """Recursively collect all parts of a string concatenation."""
        parts = []

        def collect(n) -> None:
            if isinstance(n, cst.BinaryOperation) and isinstance(n.operator, cst.Add):
                collect(n.left)
                collect(n.right)
            elif isinstance(n, cst.SimpleString):
                # Evaluate the string value
                value = self._eval_string(n)
                if value is not None:
                    parts.append({"type": "string", "value": value, "node": n})
            else:
                # This is a variable or expression
                parts.append({"type": "expr", "node": n})

        collect(node)
        return parts

    def _eval_string(self, node: cst.SimpleString) -> Optional[str]:
        """Evaluate a string literal node."""
        try:
            # Get the raw value
            raw = node.value
            if raw.startswith(("'", '"')):
                # Single or double quotes
                return ast.literal_eval(raw)
            elif raw.startswith(("'''", '"""')):
                # Triple quotes
                return ast.literal_eval(raw)
            elif raw.startswith(('r"', "r'", 'r"""', "r'''")):
                # Raw string
                return ast.literal_eval(raw[1:])
        except Exception:
            pass
        return None

    def _should_transform(self, parts: List[dict]) -> bool:
        """Check if we should transform this concatenation."""
        # Don't transform if:
        # - Only one part (no concatenation)
        # - Contains bytes literals
        # - Spans multiple lines with different quote types

        if len(parts) <= 1:
            return False

        # Check for bytes literals
        for part in parts:
            if isinstance(part["node"], cst.SimpleString):
                if part["node"].value.startswith(('b"', "b'")):
                    return False

        return True

    def _create_fstring(self, parts: List[dict]) -> Optional[cst.FormattedString]:
        """Create an f-string from parts."""
        # Build the f-string content
        content_parts = []

        for part in parts:
            if part["type"] == "string":
                # Add string content
                content_parts.append(cst.FormattedStringText(value=part["value"]))
            else:
                # Add expression
                content_parts.append(
                    cst.FormattedStringExpression(
                        expression=part["node"], conversion=None, format_spec=None
                    )
                )

        if content_parts:
            return cst.FormattedString(parts=content_parts, start='f"', end='"')

        return None


@register
class StringConcatToFString(BaseRule):
    """Convert string concatenations to f-strings."""

    rule_id = "string-concat"
    description = "Convert string concatenations to f-strings"

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        issues = []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return issues

        # Find string concatenations
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                if self._is_string_concat(node):
                    issues.append(
                        Issue(
                            rule_id=self.rule_id,
                            file=path,
                            line=node.lineno,
                            col=node.col_offset,
                            message="String concatenation can be converted to f-string",
                            severity=Severity.INFO,
                            original="string concatenation",
                        )
                    )

        return issues

    def _is_string_concat(self, node: ast.BinOp) -> bool:
        """Check if a BinOp is a string concatenation."""

        def check(n) -> Any:
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                return check(n.left) and check(n.right)
            elif (
                isinstance(n, ast.Str)
                or isinstance(n, ast.Constant)
                and isinstance(n.value, str)
            ):
                return True
            else:
                # Allow variables/expressions in the mix
                return True

        return check(node.left) and check(node.right)

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        if not issues:
            return source, []

        try:
            cst_tree = cst.parse_module(source)
        except cst.ParserSyntaxError:
            return source, []

        transformer = StringConcatTransformer()
        fixed_tree = cst_tree.visit(transformer)
        fixed_source = fixed_tree.code

        fixes = []
        for fix_info in transformer.fixes:
            fixes.append(
                Fix(
                    issue=Issue(
                        rule_id=self.rule_id,
                        file=path,
                        line=fix_info["line"],
                        col=0,
                        message="Converted string concatenation to f-string",
                        original=fix_info["original"],
                        suggested=fix_info["fixed"],
                    ),
                    file=path,
                    original_code=fix_info["original"],
                    fixed_code=fix_info["fixed"],
                    applied=True,
                )
            )

        return fixed_source, fixes

    def validate(self, path: Path, original: str, fixed: str) -> ValidationResult:
        checks = []
        errors = []

        # Check syntax
        try:
            ast.parse(fixed)
            checks.append("syntax_valid")
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")

        # Check if string concatenations remain
        try:
            tree = ast.parse(fixed)
            remaining_concats = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                    if self._is_string_concat(node):
                        remaining_concats += 1

            if remaining_concats == 0:
                checks.append("no_string_concats")
            else:
                errors.append(f"Still has {remaining_concats} string concatenations")
        except SyntaxError:
            pass

        return ValidationResult(
            file=path, passed=len(errors) == 0, checks=checks, errors=errors
        )
