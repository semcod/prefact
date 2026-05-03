"""Thread-safe LRU cache for AST parsing.

Multiple rules call ast.parse(source) on the same file content during a single
scan pass.  This module caches parsed trees by content hash so the expensive
parse is done at most once per unique source text per scan session.
"""


import ast
import threading
from collections import OrderedDict
from typing import Optional

_MAX_ENTRIES = 512

_cache: OrderedDict[int, ast.Module] = OrderedDict()
_lock = threading.Lock()


def parse_cached(source: str) -> Optional[ast.Module]:
    """Return cached ast.Module for *source*, parsing it on first call.

    Returns None on SyntaxError (same as catching SyntaxError from ast.parse).
    Cache key is hash(source); collisions are astronomically unlikely and safe
    (worst case: a cache miss triggers a fresh parse).
    """
    key = hash(source)
    with _lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    with _lock:
        _cache[key] = tree
        _cache.move_to_end(key)
        if len(_cache) > _MAX_ENTRIES:
            _cache.popitem(last=False)

    return tree


def clear() -> None:
    """Evict all entries – call after fixing a file to avoid stale trees."""
    with _lock:
        _cache.clear()
