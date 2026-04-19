"""Specialized cache for scan results."""

from pathlib import Path
from typing import Any, Optional, Tuple

from .base import Cache, CONSTANT_3600


class ScanResultCache:
    """Specialized cache for scan results."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get_key(
        self,
        file_path: Path,
        file_hash: str,
        rule_ids: Tuple[str, ...],
        config_hash: str
    ) -> str:
        """Generate cache key for scan result."""
        key_parts = [
            "scan",
            str(file_path),
            file_hash,
            ",".join(rule_ids),
            config_hash
        ]
        return ":".join(key_parts)

    def get(
        self,
        file_path: Path,
        file_hash: str,
        rule_ids: Tuple[str, ...],
        config_hash: str
    ) -> Optional[Any]:
        """Get cached scan result."""
        key = self.get_key(file_path, file_hash, rule_ids, config_hash)
        return self.cache.get(key)

    def set(
        self,
        file_path: Path,
        file_hash: str,
        rule_ids: Tuple[str, ...],
        config_hash: str,
        result: Any,
        expire: int = CONSTANT_3600  # 1 hour
    ) -> None:
        """Cache scan result."""
        key = self.get_key(file_path, file_hash, rule_ids, config_hash)
        self.cache.set(key, result, expire=expire)

    def invalidate_file(self, file_path: Path) -> None:
        """Invalidate all cache entries for a file."""
        # This is expensive - in practice, we rely on file hash changes
        pass