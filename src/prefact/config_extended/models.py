from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from prefact.config import Config, RuleConfig
from .utils import deep_merge

class ExtendedConfig(Config):
    def __init__(self, project_root=None, package_name="", include=None, exclude=None, rules=None, tools=None, performance=None, plugins=None, environments=None, **kwargs):
        super().__init__(project_root, package_name, include, exclude, rules)
        self.tools = tools or {}
        self.performance = performance or {}
        self.plugins = plugins or {}
        self.environments = environments or {}
        for key, value in kwargs.items(): setattr(self, key, value)

    @classmethod
    def from_yaml(cls, path: Path, environment: Optional[str] = None) -> "ExtendedConfig":
        if not path.exists(): return cls(project_root=Path.cwd())
        with open(path) as f: raw = yaml.safe_load(f) or {}
        if environment and "environments" in raw:
            raw = deep_merge(raw, raw["environments"].get(environment, {}))
        rules = {}
        for rule_id, rule_raw in raw.pop("rules", {}).items():
            if isinstance(rule_raw, bool): rules[rule_id] = RuleConfig(enabled=rule_raw)
            elif isinstance(rule_raw, dict):
                basic = {k: v for k, v in rule_raw.items() if k in ['enabled', 'severity', 'options']}
                rules[rule_id] = RuleConfig(**basic)
                if not hasattr(rules[rule_id], '_extended'): rules[rule_id]._extended = {k: v for k, v in rule_raw.items() if k not in ['enabled', 'severity', 'options']}
        return cls(project_root=Path(raw.pop("project_root", Path.cwd())), rules=rules, tools=raw.pop("tools", {}), performance=raw.pop("performance", {}), plugins=raw.pop("plugins", {}), environments=raw.pop("environments", {}))

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({"tools": self.tools, "performance": self.performance, "plugins": self.plugins, "environments": self.environments})
        return result