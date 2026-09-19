"""Cache for individual rule results."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

from .base import DEFAULT_CACHE_EXPIRE, Cache


@dataclass(frozen=True)
class RuleResultKey:
    """Identity of a cached rule result."""

    rule_id: str
    file_path: Path
    file_hash: str
    config_hash: str

    def as_str(self) -> str:
        """Render the underlying store key for this identity."""
        return f"rule:{self.rule_id}:{self.file_path}:{self.file_hash}:{self.config_hash}"


class RuleResultCache:
    """Cache for individual rule results."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get(self, key: RuleResultKey) -> Optional[List[Any]]:
        """Get cached rule result."""
        return self.cache.get(key.as_str())

    def set(
        self,
        key: RuleResultKey,
        issues: List[Any],
        expire: int = DEFAULT_CACHE_EXPIRE,  # 30 minutes
    ) -> None:
        """Cache rule result."""
        self.cache.set(key.as_str(), issues, expire=expire)
