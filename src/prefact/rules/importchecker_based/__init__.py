"""ImportChecker-based precise import analysis for prefact.

This package provides integration with importchecker for detailed analysis
of unused and duplicate imports with high precision.

Split from a single ``importchecker_based.py`` module into per-rule files;
this ``__init__`` re-exports every original public name so existing
``from prefact.rules.importchecker_based import ...`` call sites keep working unchanged.
It also eagerly imports every rule submodule so their ``@register`` decorators
still fire on package import, exactly as they did when all classes lived in one module.
"""

from .dependency_analysis import ImportDependencyAnalysis
from .duplicate_imports import ImportCheckerDuplicateImports
from .helper import ImportCheckerHelper
from .optimizer import ImportOptimizer
from .unused_imports import ImportCheckerUnusedImports

__all__ = [
    "ImportCheckerHelper",
    "ImportCheckerUnusedImports",
    "ImportCheckerDuplicateImports",
    "ImportDependencyAnalysis",
    "ImportOptimizer",
]
