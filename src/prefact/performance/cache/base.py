"""Base caching utilities for prefact."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

CONSTANT_1024 = 1024
MIN_1800 = 1800
CONSTANT_3600 = 3600
CONSTANT_86400 = 86400


# Constants for caching
DEFAULT_CACHE_EXPIRE = MIN_1800  # 30 minutes

try:
    import diskcache
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False

from prefact.config import Config


class Cache:
    """Wrapper for diskcache with additional functionality."""

    def __init__(self, cache_dir: Optional[Path] = None, size_limit: int = CONSTANT_1024 * CONSTANT_1024 * 100):  # 100MB
        if not DISKCACHE_AVAILABLE:
            raise ImportError("diskcache is required for caching. Install with: pip install diskcache")

        if cache_dir is None:
            cache_dir = Path.home() / ".prefact" / "cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize diskcache
        self.cache = diskcache.Cache(
            str(self.cache_dir),
            size_limit=size_limit,
            eviction_policy='least-recently-used'
        )

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        value = self.cache.get(key, default)
        if value is not default:
            self.stats["hits"] += 1
        else:
            self.stats["misses"] += 1
        return value

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set value in cache."""
        self.cache.set(key, value, expire=expire)
        self.stats["sets"] += 1

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        result = self.cache.delete(key)
        if result:
            self.stats["deletes"] += 1
        return result

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "size": self.cache.volume(),
            "count": len(self.cache),
        }

    def close(self) -> None:
        """Close cache."""
        self.cache.close()