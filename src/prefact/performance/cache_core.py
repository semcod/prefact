"""Core cache wrapper and lifecycle helpers for prefact performance caching."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

try:
    import diskcache
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False


class Cache:
    """Wrapper for diskcache with additional functionality."""

    def __init__(self, cache_dir: Optional[Path] = None, size_limit: int = 1024 * 1024 * 100):
        if not DISKCACHE_AVAILABLE:
            raise ImportError("diskcache is required for caching. Install with: pip install diskcache")

        if cache_dir is None:
            cache_dir = Path.home() / ".prefact" / "cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache = diskcache.Cache(
            str(self.cache_dir),
            size_limit=size_limit,
            eviction_policy="least-recently-used",
        )

        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}

    def get(self, key: str, default: Any = None) -> Any:
        value = self.cache.get(key, default)
        if value is not default:
            self.stats["hits"] += 1
        else:
            self.stats["misses"] += 1
        return value

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        self.cache.set(key, value, expire=expire)
        self.stats["sets"] += 1

    def delete(self, key: str) -> bool:
        result = self.cache.delete(key)
        if result:
            self.stats["deletes"] += 1
        return result

    def clear(self) -> None:
        self.cache.clear()
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}

    def get_stats(self) -> Dict[str, Any]:
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
        return {**self.stats, "hit_rate": hit_rate, "size": self.cache.volume(), "count": len(self.cache)}

    def close(self) -> None:
        self.cache.close()
