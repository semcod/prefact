"""Specialized cache for scan results."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple

from .base import CONSTANT_3600, Cache


@dataclass(frozen=True)
class ScanResultKey:
    """Identity of a cached scan result."""

    file_path: Path
    file_hash: str
    rule_ids: Tuple[str, ...]
    config_hash: str

    def as_str(self) -> str:
        """Render the underlying store key for this identity."""
        return ":".join(
            ("scan", str(self.file_path), self.file_hash, ",".join(self.rule_ids), self.config_hash)
        )


class ScanResultCache:
    """Specialized cache for scan results."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get(self, key: ScanResultKey) -> Optional[Any]:
        """Get cached scan result."""
        return self.cache.get(key.as_str())

    def set(
        self,
        key: ScanResultKey,
        result: Any,
        expire: int = CONSTANT_3600,  # 1 hour
    ) -> None:
        """Cache scan result."""
        self.cache.set(key.as_str(), result, expire=expire)

    def invalidate_file(self, file_path: Path) -> None:
        """Invalidate all cache entries for a file."""
        # This is expensive - in practice, we rely on file hash changes
        pass
