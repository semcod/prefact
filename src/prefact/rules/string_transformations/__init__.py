"""LibCST-based string concatenation to f-string transformations.

This package provides rules for converting string concatenations to f-strings
using LibCST for safe, formatting-preserving transformations.

Split from a single ``string_transformations.py`` module into three
transformer+rule pairs (``string_concat``, ``flynt_formatting``,
``context_aware_concat``); this ``__init__`` re-exports every original public
name and eagerly imports every rule submodule so their ``@register``
decorators still fire on package import, exactly as they did when all six
classes lived in one module.
"""

from .context_aware_concat import ContextAwareStringConcat, ContextAwareStringTransformer
from .flynt_formatting import MAX_LINE_LENGTH, FlyntHelper, FlyntStringFormatting
from .string_concat import StringConcatToFString, StringConcatTransformer

__all__ = [
    "MAX_LINE_LENGTH",
    "StringConcatTransformer",
    "StringConcatToFString",
    "FlyntHelper",
    "FlyntStringFormatting",
    "ContextAwareStringTransformer",
    "ContextAwareStringConcat",
]
