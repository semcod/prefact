"""Context-aware string concatenation to f-string conversion."""

from pathlib import Path
from typing import List

import libcst as cst

from prefact.config import Config
from prefact.models import Fix, Issue, ValidationResult

try:
    from prefact.rules import BaseRule, register
except ImportError:
    from .. import BaseRule, register

from .string_concat import StringConcatToFString, StringConcatTransformer


class ContextAwareStringTransformer(cst.CSTTransformer):
    """Transform string concatenations with context awareness."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.fixes = []
        self.in_function_def = False
        self.in_class_def = False
        self.current_function = None

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.in_function_def = True
        self.current_function = node.name.value
        return True

    def leave_FunctionDef(self, original_node: cst.FunctionDef) -> None:
        self.in_function_def = False
        self.current_function = None

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        self.in_class_def = True
        return True

    def leave_ClassDef(self, original_node: cst.ClassDef) -> None:
        self.in_class_def = False

    def leave_BinaryOperation(
        self,
        original_node: cst.BinaryOperation,
        updated_node: cst.BinaryOperation,
    ) -> cst.CSTNode:
        # Skip if not string concatenation
        if not isinstance(updated_node.operator, cst.Add):
            return updated_node

        # Apply context-specific rules
        if self._should_skip_context(original_node):
            return updated_node

        # Use the same transformation logic as StringConcatTransformer
        transformer = StringConcatTransformer()
        result = transformer.leave_BinaryOperation(original_node, updated_node)

        if result != updated_node:
            self.fixes.extend(transformer.fixes)

        return result

    def _should_skip_context(self, node: cst.BinaryOperation) -> bool:
        """Check if we should skip transformation based on context."""
        # Skip in __repr__ methods (often use concatenation)
        if self.current_function == "__repr__":
            return True

        # Skip in logging statements
        if self._is_in_logging_statement(node):
            return True

        # Skip if configured to skip
        if self.config.get_rule_option("string-concat", "skip_in_tests", False):
            # Check if in test file
            # (implementation depends on your project structure)
            pass

        return False

    def _is_in_logging_statement(self, node: cst.BinaryOperation) -> bool:
        """Check if this concatenation is part of a logging statement."""
        # This would need to walk up the AST to check
        # Simplified implementation
        return False


@register
class ContextAwareStringConcat(BaseRule):
    """Context-aware string concatenation to f-string conversion."""

    rule_id = "context-aware-string-concat"
    description = "Convert string concatenations to f-strings with context awareness"

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def scan_file(self, path: Path, source: str) -> List[Issue]:
        # Use the basic scanner for now
        # Context awareness is applied during fixing
        return StringConcatToFString(self.config).scan_file(path, source)

    def fix(
        self, path: Path, source: str, issues: List[Issue]
    ) -> tuple[str, List[Fix]]:
        if not issues:
            return source, []

        try:
            cst_tree = cst.parse_module(source)
        except cst.ParserSyntaxError:
            return source, []

        transformer = ContextAwareStringTransformer(self.config)
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
        return StringConcatToFString(self.config).validate(path, original, fixed)
