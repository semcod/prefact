from typing import Any, Dict, List


AUTONOMOUS_PERFORMANCE_LIMIT_KEYS = (
    "autonomous_max_examples_per_issue",
    "autonomous_max_issues",
    "autonomous_max_files_to_scan",
    "autonomous_max_issues_per_file",
    "autonomous_max_tickets",
    "autonomous_max_todo_items",
    "autonomous_max_completed_todos",
    "autonomous_max_todo_execution_items",
)


class ConfigValidator:
    @staticmethod
    def validate(config) -> List[str]:
        errors = []
        for tool_name, tool_config in config.tools.items():
            if tool_name == "ruff": errors.extend(ConfigValidator._validate_ruff_config(tool_config))
            elif tool_name == "mypy": errors.extend(ConfigValidator._validate_mypy_config(tool_config))
        errors.extend(ConfigValidator._validate_performance_config(config.performance))
        return errors

    @staticmethod
    def _validate_ruff_config(config: Dict[str, Any]) -> List[str]:
        errors = []
        if "max_line_length" in config and (not isinstance(config["max_line_length"], int) or config["max_line_length"] <= 0):
            errors.append("ruff.max_line_length must be a positive integer")
        return errors

    @staticmethod
    def _validate_mypy_config(config: Dict[str, Any]) -> List[str]:
        return ["mypy.strict must be a boolean"] if "strict" in config and not isinstance(config["strict"], bool) else []

    @staticmethod
    def _validate_performance_config(config: Dict[str, Any]) -> List[str]:
        errors = []
        for key in AUTONOMOUS_PERFORMANCE_LIMIT_KEYS:
            if key in config and (not isinstance(config[key], int) or config[key] <= 0):
                errors.append(f"performance.{key} must be a positive integer")
        return errors
