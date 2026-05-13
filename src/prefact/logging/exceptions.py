from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class PprefactException(Exception):
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.utcnow()


class ConfigurationError(PprefactException):
    pass


class RuleError(PprefactException):
    def __init__(
        self, message: str, rule_id: str, file_path: Optional[Path] = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.rule_id = rule_id
        self.file_path = file_path


class PluginError(PprefactException):
    def __init__(self, message: str, plugin_name: str, **kwargs):
        super().__init__(message, **kwargs)
        self.plugin_name = plugin_name
