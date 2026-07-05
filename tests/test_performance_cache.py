"""Regression tests for prefact.performance / performance.cache.

prefact.performance.__init__ imports CacheContext, cleanup_cache, clear_cache,
get_config_cache, get_hash_cache, get_rule_cache from .cache — an incomplete
cache.py -> cache/ package refactor had left those six names only defined in
the old, orphaned cache.py (which also collided with the cache/ package name),
so `import prefact.performance` raised ImportError.
"""

import tempfile
from pathlib import Path

import pytest

from prefact.config import Config, RuleConfig


def _config_with_cache_dir(cache_dir: Path) -> Config:
    return Config(rules={"_performance": RuleConfig(options={"cache_dir": str(cache_dir)})})


def test_prefact_performance_imports() -> None:
    """The import itself is the actual regression: it needs no diskcache
    instance, just the module-level names to exist and resolve."""
    import prefact.performance as m

    for name in (
        "Cache",
        "CacheContext",
        "cleanup_cache",
        "clear_cache",
        "get_cache",
        "get_config_cache",
        "get_hash_cache",
        "get_rule_cache",
        "get_scan_cache",
        "initialize_cache",
    ):
        assert hasattr(m, name), f"prefact.performance is missing {name}"


def test_cache_context_lifecycle() -> None:
    pytest.importorskip("diskcache")
    from prefact.performance import (
        CacheContext,
        clear_cache,
        get_cache,
        get_config_cache,
        get_hash_cache,
        get_rule_cache,
    )

    with tempfile.TemporaryDirectory() as tmp:
        config = _config_with_cache_dir(Path(tmp))
        with CacheContext(config):
            get_cache().set("k", "v")
            assert get_cache().get("k") == "v"
            assert get_config_cache() is not None
            assert get_rule_cache() is not None
            assert get_hash_cache() is not None

            clear_cache()
            assert get_cache().get("k") is None

    # cleanup_cache() (run on __exit__) must reset the globals so a stale
    # instance from this test can't leak into another test/process.
    with pytest.raises(RuntimeError):
        get_cache()
