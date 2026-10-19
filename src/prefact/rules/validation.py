"""Validation helpers for prefact rules."""

import ast
from pathlib import Path

try:
    from prefact.models import ValidationResult
except ImportError:
    from ..models import ValidationResult


def validate_syntax(
    path: Path,
    original_or_fixed: str = "",
    fixed: str | None = None,
) -> ValidationResult:
    """Validate that fixed source code has valid Python syntax."""
    code_to_check = fixed if fixed is not None else original_or_fixed
    checks: list[str] = []
    errors: list[str] = []
    try:
        ast.parse(code_to_check)
        checks.append("syntax_valid")
    except SyntaxError as exc:
        errors.append(f"SyntaxError: {exc}")
    return ValidationResult(
        file=path, passed=not errors, checks=checks, errors=errors
    )
