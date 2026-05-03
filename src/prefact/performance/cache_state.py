"""Global cache state and public cache initialization helpers."""

from typing import Optional

from prefact.config import Config

from .cache_adapters import ConfigCache, FileHashCache, RuleResultCache, ScanResultCache
from .cache_core import Cache

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
    size_limit = config.get_rule_option("_performance", "cache_size", 100 * 1024 * 1024)

    _cache = Cache(cache_dir, size_limit)
    _scan_cache = ScanResultCache(_cache)
    _config_cache = ConfigCache(_cache)
    _rule_cache = RuleResultCache(_cache)
    _hash_cache = FileHashCache(_cache)


def get_cache() -> Cache:
    if _cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _cache


def get_scan_cache() -> ScanResultCache:
    if _scan_cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _scan_cache


def get_config_cache() -> ConfigCache:
    if _config_cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _config_cache


def get_rule_cache() -> RuleResultCache:
    if _rule_cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _rule_cache


def get_hash_cache() -> FileHashCache:
    if _hash_cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _hash_cache


def close_cache() -> None:
    global _cache, _scan_cache, _config_cache, _rule_cache, _hash_cache
    if _cache is not None:
        _cache.close()
    _cache = None
    _scan_cache = None
    _config_cache = None
    _rule_cache = None
    _hash_cache = None
