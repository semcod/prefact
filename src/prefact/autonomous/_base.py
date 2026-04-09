"""Base utilities for autonomous modules."""

from pathlib import Path
from typing import Dict, Optional

from prefact.config_extended import ExtendedConfig

from rich.console import Console

# Shared console instance
console = Console()

# Constants for code analysis
MIN_CODE_SIZE = 50
HASH_BLOCK_SIZE = 65536
DEFAULT_AUTONOMOUS_LIMITS = {
    "autonomous_max_examples_per_issue": 3,
    "autonomous_max_issues": 500,
    "autonomous_max_files_to_scan": 1000,
    "autonomous_max_issues_per_file": 50,
    "autonomous_max_run_seconds": 300,
    "autonomous_max_tickets": 100,
    "autonomous_max_todo_items": 200,
    "autonomous_max_completed_todos": 100,
    "autonomous_max_todo_execution_items": 50,
}


class BaseManager:
    """Base class for autonomous managers."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.refact_config_path = project_root / "prefact.yaml"
        self.planfile_path = project_root / "planfile.yaml"
        self.todo_path = project_root / "TODO.md"
        self.changelog_path = project_root / "CHANGELOG.md"
        self.examples_dir = project_root / "examples"
        self._autonomous_limits: Optional[Dict[str, int]] = None
        self._autonomous_limits_mtime: Optional[float] = None

    def get_autonomous_limit(self, key: str) -> int:
        return self._load_autonomous_limits()[key]

    def _load_autonomous_limits(self) -> Dict[str, int]:
        config_mtime = self.refact_config_path.stat().st_mtime if self.refact_config_path.exists() else None
        if self._autonomous_limits is not None and self._autonomous_limits_mtime == config_mtime:
            return self._autonomous_limits

        limits = DEFAULT_AUTONOMOUS_LIMITS.copy()

        if self.refact_config_path.exists():
            try:
                config = ExtendedConfig.from_yaml(self.refact_config_path)
            except Exception:
                config = None

            if config is not None:
                for limit_key, default_value in DEFAULT_AUTONOMOUS_LIMITS.items():
                    configured_value = config.performance.get(limit_key, default_value)
                    if isinstance(configured_value, int) and configured_value > 0:
                        limits[limit_key] = configured_value

        self._autonomous_limits = limits
        self._autonomous_limits_mtime = config_mtime
        return self._autonomous_limits
