"""Constants and defaults for extended configuration handling."""

CONSTANT_3 = 3
CONSTANT_4 = 4
CONSTANT_8 = 8
CONSTANT_88 = 88
CONSTANT_104857600 = 104857600

DEFAULT_CACHE_SIZE = CONSTANT_104857600  # 100MB
DEFAULT_MAX_LINE_LENGTH = CONSTANT_88

DEFAULT_INCLUDE = ["**/*.py"]
DEFAULT_EXCLUDE = [
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/.venv/**",
    "**/venv/**",
    "**/.git/**",
    "**/build/**",
    "**/dist/**",
    "**/*.egg-info/**",
]

RULE_BASIC_FIELDS = {"enabled", "severity", "options"}
