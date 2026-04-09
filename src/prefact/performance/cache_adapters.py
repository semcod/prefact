"""Specialized cache adapters for prefact performance caching."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from prefact.config import Config

from .cache_core import Cache

DEFAULT_CACHE_EXPIRE = 1800
CONSTANT_1024 = 1024
CONSTANT_1800 = 1800
CONSTANT_3600 = 3600
CONSTANT_86400 = 86400


class ScanResultCache:
    """Specialized cache for scan results."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get_key(self, file_path: Path, file_hash: str, rule_ids: tuple[str, ...], config_hash: str) -> str:
        return ":".join(["scan", str(file_path), file_hash, ",".join(rule_ids), config_hash])

    def get(self, file_path: Path, file_hash: str, rule_ids: tuple[str, ...], config_hash: str) -> Optional[Any]:
        return self.cache.get(self.get_key(file_path, file_hash, rule_ids, config_hash))

    def set(
        self,
        file_path: Path,
        file_hash: str,
        rule_ids: tuple[str, ...],
        config_hash: str,
        result: Any,
        expire: int = CONSTANT_3600,
    ) -> None:
        self.cache.set(self.get_key(file_path, file_hash, rule_ids, config_hash), result, expire=expire)

    def invalidate_file(self, file_path: Path) -> None:
        pass


class ConfigCache:
    """Cache for rule configurations."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get_key(self, config: Config) -> str:
        config_str = json.dumps(config.to_dict(), sort_keys=True)
        return f"config:{hashlib.md5(config_str.encode()).hexdigest()}"

    def get(self, config: Config) -> Optional[Dict[str, Any]]:
        return self.cache.get(self.get_key(config))

    def set(self, config: Config, processed_config: Dict[str, Any]) -> None:
        self.cache.set(self.get_key(config), processed_config, expire=CONSTANT_86400)


class RuleResultCache:
    """Cache for individual rule results."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get_key(self, rule_id: str, file_path: Path, file_hash: str, config_hash: str) -> str:
        return f"rule:{rule_id}:{file_path}:{file_hash}:{config_hash}"

    def get(self, rule_id: str, file_path: Path, file_hash: str, config_hash: str) -> Optional[List[Any]]:
        return self.cache.get(self.get_key(rule_id, file_path, file_hash, config_hash))

    def set(
        self,
        rule_id: str,
        file_path: Path,
        file_hash: str,
        config_hash: str,
        issues: List[Any],
        expire: int = DEFAULT_CACHE_EXPIRE,
    ) -> None:
        self.cache.set(self.get_key(rule_id, file_path, file_hash, config_hash), issues, expire=expire)


class FileHashCache:
    """Cache for file hashes."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get_hash(self, file_path: Path) -> Optional[str]:
        key = f"hash:{file_path}"
        mtime = file_path.stat().st_mtime
        cached = self.cache.get(key)
        if cached and cached.get("mtime") == mtime:
            return cached.get("hash")
        return None

    def set_hash(self, file_path: Path, file_hash: str) -> None:
        key = f"hash:{file_path}"
        mtime = file_path.stat().st_mtime
        self.cache.set(key, {"hash": file_hash, "mtime": mtime}, expire=CONSTANT_86400)
