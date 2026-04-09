"""Validation utilities for extended configuration objects."""

from typing import Any, Dict, List

from .config import ExtendedConfig


class ConfigValidator:
    """Validate configuration files."""

    @staticmethod
    def validate(config: ExtendedConfig) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        for tool_name, tool_config in config.tools.items():
            if tool_name == "ruff":
                errors.extend(ConfigValidator._validate_ruff_config(tool_config))
            elif tool_name == "mypy":
                errors.extend(ConfigValidator._validate_mypy_config(tool_config))
            elif tool_name == "isort":
                errors.extend(ConfigValidator._validate_isort_config(tool_config))
        errors.extend(ConfigValidator._validate_performance_config(config.performance))
        for rule_id, rule_config in config.rules.items():
            errors.extend(ConfigValidator._validate_rule_config(rule_id, rule_config))
        return errors

    @staticmethod
    def _validate_ruff_config(config: Dict[str, Any]) -> List[str]:
        errors = []
        if "max_line_length" in config:
            if not isinstance(config["max_line_length"], int) or config["max_line_length"] <= 0:
                errors.append("ruff.max_line_length must be a positive integer")
        if "select" in config:
            if not isinstance(config["select"], list):
                errors.append("ruff.select must be a list")
        return errors

    @staticmethod
    def _validate_mypy_config(config: Dict[str, Any]) -> List[str]:
        errors = []
        if "strict" in config:
            if not isinstance(config["strict"], bool):
                errors.append("mypy.strict must be a boolean")
        return errors

    @staticmethod
    def _validate_isort_config(config: Dict[str, Any]) -> List[str]:
        errors = []
        if "profile" in config and not isinstance(config["profile"], str):
            errors.append("isort.profile must be a string")
        return errors

    @staticmethod
    def _validate_performance_config(config: Dict[str, Any]) -> List[str]:
        errors = []
        if "cache_size" in config and (not isinstance(config["cache_size"], int) or config["cache_size"] <= 0):
            errors.append("performance.cache_size must be a positive integer")
        return errors

    @staticmethod
    def _validate_rule_config(rule_id: str, rule_config: Any) -> List[str]:
        errors = []
        if rule_config is None:
            errors.append(f"{rule_id} is invalid")
        return errors
