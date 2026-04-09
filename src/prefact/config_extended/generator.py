"""Configuration generator — extracted from config_extended.py for package compat."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .constants import DEFAULT_CACHE_SIZE, DEFAULT_MAX_LINE_LENGTH

DEFAULT_AUTONOMOUS_LIMITS = {
    "autonomous_max_examples_per_issue": 3,
    "autonomous_max_issues": 500,
    "autonomous_max_files_to_scan": 1000,
    "autonomous_max_issues_per_file": 50,
    "autonomous_max_tickets": 100,
    "autonomous_max_todo_items": 200,
    "autonomous_max_completed_todos": 100,
    "autonomous_max_todo_execution_items": 50,
}


class ConfigGenerator:
    """Generate configuration files."""

    @staticmethod
    def generate_extended_config(
        project_root: Path,
        tools: Optional[List[str]] = None,
        rules: Optional[List[str]] = None,
    ) -> str:
        """Generate an extended prefact.yaml configuration."""
        if tools is None:
            tools = ["ruff", "mypy", "isort"]

        if rules is None:
            rules = ["unused-imports", "relative-imports", "missing-return-type"]

        config: Dict[str, Any] = {
            "project_root": str(project_root),
            "package_name": project_root.name,
            "include": ["**/*.py"],
            "exclude": [
                "**/__pycache__/**",
                "**/node_modules/**",
                "**/.venv/**",
                "**/venv/**",
                "**/.git/**",
                "**/build/**",
                "**/dist/**",
                "**/*.egg-info/**",
                "**/tests/**",
            ],
            "tools": {
                "parallel": True,
                "cache": True,
            },
            "performance": {
                "max_workers": 4,
                "cache_size": DEFAULT_CACHE_SIZE,
                "chunk_size": 10,
                **DEFAULT_AUTONOMOUS_LIMITS,
            },
            "rules": {},
            "plugins": {
                "enabled": True,
                "directories": [
                    "~/.prefact/plugins",
                    "./.prefact/plugins",
                ],
            },
            "environments": {
                "development": {
                    "rules": {
                        "print-statements": {"enabled": True},
                        "magic-numbers": {"enabled": False},
                    },
                    "performance": {"max_workers": 2},
                },
                "production": {
                    "rules": {
                        "print-statements": {"enabled": False},
                        "magic-numbers": {"enabled": True},
                    },
                    "performance": {"max_workers": 8},
                },
            },
        }

        if "ruff" in tools:
            config["tools"]["ruff"] = {
                "enabled": True,
                "max_line_length": DEFAULT_MAX_LINE_LENGTH,
                "select": ["E", "F", "W", "I"],
                "ignore": ["E501"],
            }

        if "mypy" in tools:
            config["tools"]["mypy"] = {
                "enabled": True,
                "strict": False,
                "ignore_missing_imports": True,
            }

        if "isort" in tools:
            config["tools"]["isort"] = {
                "enabled": True,
                "profile": "black",
                "multi_line_output": 3,
            }

        for rule_id in rules:
            if rule_id == "unused-imports":
                config["rules"][rule_id] = {
                    "enabled": True,
                    "tools": ["ruff", "autoflake"],
                    "severity": "error",
                }
            elif rule_id == "relative-imports":
                config["rules"][rule_id] = {
                    "enabled": True,
                    "tools": ["libcst"],
                    "auto_fix": True,
                }
            elif rule_id == "missing-return-type":
                config["rules"][rule_id] = {
                    "enabled": True,
                    "tools": ["mypy"],
                    "severity": "warning",
                }
            elif rule_id == "llm-hallucinations":
                config["rules"][rule_id] = {
                    "enabled": True,
                    "patterns": [
                        {"pattern": "TODO: implement", "severity": "warning"},
                        {"pattern": "placeholder", "severity": "error"},
                    ],
                }
            elif rule_id == "magic-numbers":
                config["rules"][rule_id] = {
                    "enabled": True,
                    "threshold": 10,
                    "allowed_numbers": [0, 1, -1, 2, 10, 100],
                }

        return yaml.dump(config, default_flow_style=False, sort_keys=False)

    @staticmethod
    def generate_composite_rule_config(
        name: str,
        description: str,
        tools: List[str],
        strategy: str = "parallel",
    ) -> Dict[str, Any]:
        """Generate configuration for a composite rule."""
        return {
            "id": f"composite-{name}",
            "description": description,
            "enabled": True,
            "tools": tools,
            "strategy": strategy,
            "tool_priorities": {tool: i for i, tool in enumerate(tools)},
        }

    @staticmethod
    def save_config(config: Dict[str, Any], output_path: Path) -> None:
        """Save configuration to YAML file."""
        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
