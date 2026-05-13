"""Cache for rule configurations."""

import hashlib
import json
from typing import Any, Dict, Optional

from prefact.config import Config

from .base import CONSTANT_86400, Cache


class ConfigCache:
    """Cache for rule configurations."""

    def __init__(self, cache: Cache):
        self.cache = cache

    def get_key(self, config: Config) -> str:
        """Generate cache key for configuration."""
        config_dict = config.to_dict()
        config_str = json.dumps(config_dict, sort_keys=True)
        return f"config:{hashlib.md5(config_str.encode()).hexdigest()}"

    def get(self, config: Config) -> Optional[Dict[str, Any]]:
        """Get cached configuration."""
        key = self.get_key(config)
        return self.cache.get(key)

    def set(self, config: Config, processed_config: Dict[str, Any]) -> None:
        """Cache processed configuration."""
        key = self.get_key(config)
        self.cache.set(key, processed_config, expire=CONSTANT_86400)  # 24 hours
