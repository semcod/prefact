"""Canonical defaults for prefact configuration.

Single source of truth for include/exclude patterns used across
Config, ExtendedConfig, ConfigGenerator, and the ``prefact init`` template.
"""

DEFAULT_INCLUDE: list[str] = ["**/*.py"]

DEFAULT_EXCLUDE: list[str] = [
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/.venv/**",
    "**/.venv*/**",
    "**/venv/**",
    "**/venv*/**",
    "**/env/**",
    "**/.git/**",
    "**/build/**",
    "**/dist/**",
    "**/*.egg-info/**",
]
