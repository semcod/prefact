"""Global cache instances and initialization."""

from typing import Optional

from prefact.config import Config

from .base import CONSTANT_1024, Cache
from .config import ConfigCache
from .hash import FileHashCache
from .rule import RuleResultCache
from .scan import ScanResultCache

# Global cache instance
_cache: Optional[Cache] = None
_scan_cache: Optional[ScanResultCache] = None
_config_cache: Optional[ConfigCache] = None
_rule_cache: Optional[RuleResultCache] = None
_hash_cache: Optional[FileHashCache] = None


def initialize_cache(config: Config) -> None:
    """Initialize the cache system."""
    global _cache, _scan_cache, _config_cache, _rule_cache, _hash_cache

    if not config.get_rule_option("_performance", "cache", True):
        return

    cache_dir = config.get_rule_option("_performance", "cache_dir")
    size_limit = config.get_rule_option(
        "_performance", "cache_size", 100 * CONSTANT_1024 * CONSTANT_1024
    )

    _cache = Cache(cache_dir, size_limit)
    _scan_cache = ScanResultCache(_cache)
    _config_cache = ConfigCache(_cache)
    _rule_cache = RuleResultCache(_cache)
    _hash_cache = FileHashCache(_cache)


def get_cache() -> Cache:
    """Get the global cache instance."""
    if _cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _cache


def get_scan_cache() -> ScanResultCache:
    """Get the scan result cache instance."""
    if _scan_cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _scan_cache


def get_config_cache() -> ConfigCache:
    """Get the configuration cache instance."""
    if _config_cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _config_cache


def get_rule_cache() -> RuleResultCache:
    """Get the rule result cache instance."""
    if _rule_cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _rule_cache


def get_hash_cache() -> FileHashCache:
    """Get the file hash cache instance."""
    if _hash_cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _hash_cache


def cleanup_cache() -> None:
    """Close the cache and clear all global instances."""
    global _cache, _scan_cache, _config_cache, _rule_cache, _hash_cache

    if _cache:
        _cache.close()

    _cache = None
    _scan_cache = None
    _config_cache = None
    _rule_cache = None
    _hash_cache = None


def clear_cache(pattern: Optional[str] = None) -> None:
    """Clear cache entries, optionally only those whose key contains `pattern`."""
    cache = get_cache()

    if pattern:
        keys_to_delete = [key for key in cache.cache.iterkeys() if pattern in key]
        for key in keys_to_delete:
            cache.delete(key)
    else:
        cache.clear()


class CacheContext:
    """Context manager that initializes the cache on entry and cleans it up on exit."""

    def __init__(self, config: Config):
        self.config = config

    def __enter__(self) -> "CacheContext":
        initialize_cache(self.config)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        cleanup_cache()
