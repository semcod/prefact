"""prefact.rules

Registry for prefact rules.

The registry uses lazy loading to avoid importing all rule modules at startup,
significantly improving CLI cold-start performance.

Usage:
    from prefact.rules import get_rule, get_all_rules

    # Get a specific rule class
    rule_class = get_rule("unused-imports")

    # Get all rule classes (loads them all)
    all_rules = get_all_rules()
"""

import abc
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prefact.config import Config
    from prefact.models import Fix, Issue, ValidationResult


class BaseRule(abc.ABC):
    """Base class every prefactoring rule must implement."""

    rule_id: str = ""
    description: str = ""

    def __init__(self, config: "Config") -> None:
        self.config = config

    @abc.abstractmethod
    def scan_file(self, path: Path, source: str) -> list["Issue"]:
        """Return list of issues found in *source*."""

    @abc.abstractmethod
    def fix(
        self, path: Path, source: str, issues: list["Issue"]
    ) -> tuple[str, list["Fix"]]:
        """Return (fixed_source, list_of_fixes)."""

    @abc.abstractmethod
    def validate(self, path: Path, original: str, fixed: str) -> "ValidationResult":
        """Check that the fix didn't break anything."""

    def _validate_by_rescan(
        self,
        path: Path,
        original: str,
        fixed: str,
        check_name: str,
        error_template: str,
    ) -> "ValidationResult":
        """Re-scan *fixed* and return a ValidationResult using *check_name* and *error_template*."""
        from prefact.models import ValidationResult

        issues = self.scan_file(path, fixed)
        return ValidationResult(
            file=path,
            passed=len(issues) == 0,
            checks=[check_name] if not issues else [],
            errors=[error_template.format(count=len(issues))] if issues else [],
        )


# Import lazy registry
from prefact.rules.registry import get_all_rules as _get_all_rules
from prefact.rules.registry import get_rule as _get_rule
from prefact.rules.registry import register as _register


def register(cls: type["BaseRule"]) -> type["BaseRule"]:
    """Decorator that registers a rule class."""
    return _register(cls)


def get_all_rules() -> dict[str, type["BaseRule"]]:
    """Get all registered rule classes (loads them all)."""
    return _get_all_rules()


def get_rule(rule_id: str) -> type["BaseRule"]:
    """Get a rule class by ID (loads it if necessary)."""
    return _get_rule(rule_id)


# Force-import concrete rules so they self-register.
from prefact.rules.duplicate_imports import DuplicateImports as _r3  # noqa: F401, E402
from prefact.rules.print_statements import PrintStatements as _r7  # noqa: F401, E402
from prefact.rules.relative_imports import (
    RelativeToAbsoluteImports as _r1,  # noqa: F401, E402
)
from prefact.rules.sorted_imports import SortedImports as _r5  # noqa: F401, E402
from prefact.rules.string_concat import StringConcatToFstring as _r6  # noqa: F401, E402
from prefact.rules.type_hints import MissingReturnType as _r8  # noqa: F401, E402
from prefact.rules.unused_imports import UnusedImports as _r2  # noqa: F401, E402
from prefact.rules.wildcard_imports import WildcardImports as _r4  # noqa: F401, E402

# Import new integration rules so they self-register
# Only import if dependencies are available
try:
    from prefact.rules.ruff_based import (  # noqa: F401, E402
        RuffDuplicateImports as _ruff_1,
    )
    from prefact.rules.ruff_based import (
        RuffPrintStatements as _ruff_2,
    )
    from prefact.rules.ruff_based import (
        RuffSortedImports as _ruff_3,
    )
    from prefact.rules.ruff_based import (
        RuffUnusedImports as _ruff_4,
    )
    from prefact.rules.ruff_based import (
        RuffWildcardImports as _ruff_5,
    )
except ImportError:
    pass

try:
    from prefact.rules.mypy_based import (  # noqa: F401, E402
        MyPyMissingReturnType as _mypy_1,
    )
    from prefact.rules.mypy_based import (
        MyPyTypeChecking as _mypy_2,
    )
    from prefact.rules.mypy_based import (
        SmartReturnTypeRule as _mypy_3,
    )
except ImportError:
    pass

try:
    from prefact.rules.isort_based import (
        CustomImportOrganization as _isort_3,
    )
    from prefact.rules.isort_based import (
        ImportSectionSeparator as _isort_2,
    )
    from prefact.rules.isort_based import (  # noqa: F401, E402
        ISortedImports as _isort_1,
    )
except ImportError:
    pass

try:
    from prefact.rules.autoflake_based import (
        AutoflakeAll as _autoflake_4,
    )
    from prefact.rules.autoflake_based import (
        AutoflakeDuplicateKeys as _autoflake_3,
    )
    from prefact.rules.autoflake_based import (  # noqa: F401, E402
        AutoflakeUnusedImports as _autoflake_1,
    )
    from prefact.rules.autoflake_based import (
        AutoflakeUnusedVariables as _autoflake_2,
    )
except ImportError:
    pass

try:
    from prefact.rules.string_transformations import (
        ContextAwareStringConcat as _string_3,
    )
    from prefact.rules.string_transformations import (
        FlyntStringFormatting as _string_2,
    )
    from prefact.rules.string_transformations import (  # noqa: F401, E402
        StringConcatToFString as _string_1,
    )
except ImportError:
    pass

try:
    from prefact.rules.pylint_based import (
        PylintComprehensive as _pylint_3,
    )
    from prefact.rules.pylint_based import (  # noqa: F401, E402
        PylintPrintStatements as _pylint_1,
    )
    from prefact.rules.pylint_based import (
        PylintStringConcat as _pylint_2,
    )
except ImportError:
    pass

try:
    from prefact.rules.unimport_based import (
        UnimportAll as _unimport_4,
    )
    from prefact.rules.unimport_based import (
        UnimportDuplicateImports as _unimport_2,
    )
    from prefact.rules.unimport_based import (
        UnimportStarImports as _unimport_3,
    )
    from prefact.rules.unimport_based import (  # noqa: F401, E402
        UnimportUnusedImports as _unimport_1,
    )
except ImportError:
    pass

try:
    from prefact.rules.importchecker_based import (
        ImportCheckerDuplicateImports as _ic_2,
    )
    from prefact.rules.importchecker_based import (  # noqa: F401, E402
        ImportCheckerUnusedImports as _ic_1,
    )
    from prefact.rules.importchecker_based import (
        ImportDependencyAnalysis as _ic_3,
    )
    from prefact.rules.importchecker_based import (
        ImportOptimizer as _ic_4,
    )
except ImportError:
    pass

try:
    from prefact.rules.import_linter_based import (
        ImportLinterCustomArchitecture as _il_4,
    )
    from prefact.rules.import_linter_based import (
        ImportLinterIndependence as _il_3,
    )
    from prefact.rules.import_linter_based import (  # noqa: F401, E402
        ImportLinterLayers as _il_1,
    )
    from prefact.rules.import_linter_based import (
        ImportLinterNoRelative as _il_2,
    )
except ImportError:
    pass
# Import composite rules from new modules
from prefact.rules.ai_boilerplate import AIBoilerplateRule as _llm_4  # noqa: F401, E402
from prefact.rules.composite_rules import (
    CompositeImportRules as _comp_2,
)
from prefact.rules.composite_rules import (
    CompositeTypeChecking as _comp_3,
)
from prefact.rules.composite_rules import (  # noqa: F401, E402
    CompositeUnusedImports as _comp_1,
)
from prefact.rules.llm_generated_code import (
    LLMGeneratedCodeRule as _llm_3,  # noqa: F401, E402
)
from prefact.rules.llm_hallucinations import (
    LLMHallucinationRule as _llm_1,  # noqa: F401, E402
)
from prefact.rules.magic_numbers import MagicNumberRule as _llm_2  # noqa: F401, E402
