"""Extended configuration model and helpers."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from prefact.config import Config, RuleConfig
from .constants import DEFAULT_EXCLUDE, DEFAULT_INCLUDE


class ExtendedConfig(Config):
    """Extended configuration with additional features."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        package_name: str = "",
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        rules: Optional[Dict[str, Any]] = None,
        tools: Optional[Dict[str, Any]] = None,
        performance: Optional[Dict[str, Any]] = None,
        plugins: Optional[Dict[str, Any]] = None,
        environments: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(project_root, package_name, include, exclude, rules)
        self.tools: Dict[str, Any] = tools or {}
        self.performance: Dict[str, Any] = performance or {}
        self.plugins: Dict[str, Any] = plugins or {}
        self.environments: Dict[str, Any] = environments or {}
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def from_yaml(cls, path: Path, environment: Optional[str] = None) -> "ExtendedConfig":
        """Load configuration from YAML file with environment support."""
        if not path.exists():
            return cls(project_root=Path.cwd())

        with open(path) as f:
            raw = yaml.safe_load(f) or {}

        if environment and "environments" in raw:
            env_config = raw["environments"].get(environment, {})
            raw = cls._deep_merge(raw, env_config)

        rules = cls._parse_rules(raw.pop("rules", {}))
        tools = raw.pop("tools", {})
        performance = raw.pop("performance", {})
        plugins = raw.pop("plugins", {})
        environments = raw.pop("environments", {})
        defaults_include = raw.pop("include", DEFAULT_INCLUDE)
        defaults_exclude = raw.pop("exclude", DEFAULT_EXCLUDE)

        return cls(
            project_root=Path(raw.pop("project_root", Path.cwd())),
            package_name=raw.pop("package_name", ""),
            include=raw.pop("include", defaults_include),
            exclude=raw.pop("exclude", defaults_exclude),
            rules=rules,
            tools=tools,
            performance=performance,
            plugins=plugins,
            environments=environments,
            **{k: v for k, v in raw.items() if k in cls.__dataclass_fields__},
        )

    @staticmethod
    def _parse_rules(rules_raw: Dict[str, Any]) -> Dict[str, RuleConfig]:
        """Parse rules from raw configuration."""
        rules = {}
        for rule_id, rule_raw in rules_raw.items():
            if isinstance(rule_raw, bool):
                rules[rule_id] = RuleConfig(enabled=rule_raw)
            elif isinstance(rule_raw, dict):
                basic_fields = {k: v for k, v in rule_raw.items() if k in {"enabled", "severity", "options"}}
                rules[rule_id] = RuleConfig(**basic_fields)
                if hasattr(rules[rule_id], "_extended"):
                    rules[rule_id]._extended.update(rule_raw)
                else:
                    rules[rule_id]._extended = {k: v for k, v in rule_raw.items() if k not in {"enabled", "severity", "options"}}
        return rules

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ExtendedConfig._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        return self.tools.get(tool_name, {})

    def get_performance_setting(self, key: str, default: Any = None) -> Any:
        return self.performance.get(key, default)

    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        return self.plugins.get(plugin_name, {})

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update(
            {
                "tools": self.tools,
                "performance": self.performance,
                "plugins": self.plugins,
                "environments": self.environments,
            }
        )
        return result
