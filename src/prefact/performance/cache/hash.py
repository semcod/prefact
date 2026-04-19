"""Cache for file hashes."""

from pathlib import Path
from typing import Optional

from .base import Cache, CONSTANT_86400


class FileHashCache:
    """Cache for file hashes."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get_hash(self, file_path: Path) -> Optional[str]:
        """Get cached file hash."""
        key = f"hash:{file_path}"
        mtime = file_path.stat().st_mtime

        cached = self.cache.get(key)
        if cached and cached.get("mtime") == mtime:
            return cached.get("hash")

        return None

    def set_hash(self, file_path: Path, file_hash: str) -> None:
        """Cache file hash with mtime."""
        key = f"hash:{file_path}"
        mtime = file_path.stat().st_mtime

        self.cache.set(key, {"hash": file_hash, "mtime": mtime}, expire=CONSTANT_86400)