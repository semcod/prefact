"""Thread-safe LRU cache for AST parsing.

Multiple rules call ast.parse(source) on the same file content during a single
scan pass. This module caches parsed trees so the expensive parse is done at most
once per unique source text per scan session.
"""

import ast
import functools
from typing import Optional


@functools.lru_cache(maxsize=2048)
def parse_cached(source: str) -> Optional[ast.Module]:
    """Return cached ast.Module for *source*, parsing it on first call.

    Returns None on SyntaxError (same as catching SyntaxError from ast.parse).
    """
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def clear() -> None:
    """Evict all entries – call after fixing a file to avoid stale trees."""
    parse_cached.cache_clear()
