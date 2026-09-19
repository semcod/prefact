"""Specialized cache for scan results."""

from pathlib import Path
from typing import Any, NamedTuple, Optional, Tuple

from .base import CONSTANT_3600, Cache


class ScanCacheKey(NamedTuple):
    """Identity of a cached scan result."""

    file_path: Path
    file_hash: str
    rule_ids: Tuple[str, ...]
    config_hash: str


class ScanResultCache:
    """Specialized cache for scan results."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get_key(self, key: ScanCacheKey) -> str:
        """Generate cache key for scan result."""
        return f"scan:{key.file_path}:{key.file_hash}:{','.join(key.rule_ids)}:{key.config_hash}"

    def get(self, key: ScanCacheKey) -> Optional[Any]:
        """Get cached scan result."""
        return self.cache.get(self.get_key(key))

    def set(
        self,
        key: ScanCacheKey,
        result: Any,
        expire: int = CONSTANT_3600,  # 1 hour
    ) -> None:
        """Cache scan result."""
        self.cache.set(self.get_key(key), result, expire=expire)

    def invalidate_file(self, file_path: Path) -> None:
        """Invalidate all cache entries for a file."""
        # This is expensive - in practice, we rely on file hash changes
        pass
