"""ISort-based import sorting rules for prefact.

This package provides integration with ISort for sorting and organizing imports
according to PEP8 conventions.

Split from a single ``isort_based.py`` module into per-rule files; this
``__init__`` re-exports every original public name (including ``HAS_ISORT``
and the underscore-prefixed helper) so existing ``from prefact.rules.isort_based
import ...`` call sites keep working unchanged. It also eagerly imports every
rule submodule so their ``@register`` decorators still fire on package import,
exactly as they did when all four classes lived in one module.
"""

from .custom_organization import CustomImportOrganization
from .helper import HAS_ISORT, ISortHelper
from .section_separator import ImportSectionSeparator
from .sorted_imports import ISortedImports

__all__ = [
    "HAS_ISORT",
    "ISortHelper",
    "ISortedImports",
    "ImportSectionSeparator",
    "CustomImportOrganization",
]
