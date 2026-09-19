"""Cache for individual rule results."""

from pathlib import Path
from typing import Any, List, NamedTuple, Optional

from .base import DEFAULT_CACHE_EXPIRE, Cache


class RuleCacheKey(NamedTuple):
    """Identity of a cached rule result."""

    rule_id: str
    file_path: Path
    file_hash: str
    config_hash: str


class RuleResultCache:
    """Cache for individual rule results."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get_key(self, key: RuleCacheKey) -> str:
        """Generate cache key for rule result."""
        return f"rule:{key.rule_id}:{key.file_path}:{key.file_hash}:{key.config_hash}"

    def get(self, key: RuleCacheKey) -> Optional[List[Any]]:
        """Get cached rule result."""
        return self.cache.get(self.get_key(key))

    def set(
        self,
        key: RuleCacheKey,
        issues: List[Any],
        expire: int = DEFAULT_CACHE_EXPIRE,  # 30 minutes
    ) -> None:
        """Cache rule result."""
        self.cache.set(self.get_key(key), issues, expire=expire)
