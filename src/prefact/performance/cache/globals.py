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
