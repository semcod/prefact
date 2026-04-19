"""Cache for individual rule results."""

from pathlib import Path
from typing import Any, List, Optional

from .base import Cache, DEFAULT_CACHE_EXPIRE


class RuleResultCache:
    """Cache for individual rule results."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get_key(
        self,
        rule_id: str,
        file_path: Path,
        file_hash: str,
        config_hash: str
    ) -> str:
        """Generate cache key for rule result."""
        return f"rule:{rule_id}:{file_path}:{file_hash}:{config_hash}"

    def get(
        self,
        rule_id: str,
        file_path: Path,
        file_hash: str,
        config_hash: str
    ) -> Optional[List[Any]]:
        """Get cached rule result."""
        key = self.get_key(rule_id, file_path, file_hash, config_hash)
        return self.cache.get(key)

    def set(
        self,
        rule_id: str,
        file_path: Path,
        file_hash: str,
        config_hash: str,
        issues: List[Any],
        expire: int = DEFAULT_CACHE_EXPIRE  # 30 minutes
    ) -> None:
        """Cache rule result."""
        key = self.get_key(rule_id, file_path, file_hash, config_hash)
        self.cache.set(key, issues, expire=expire)