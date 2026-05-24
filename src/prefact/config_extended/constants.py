"""Constants and defaults for extended configuration handling."""

from prefact.defaults import DEFAULT_EXCLUDE, DEFAULT_INCLUDE  # noqa: F401  re-exported

CONSTANT_3 = 3
CONSTANT_4 = 4
CONSTANT_8 = 8
CONSTANT_88 = 88
CONSTANT_104857600 = 104857600

DEFAULT_CACHE_SIZE = CONSTANT_104857600  # 100MB
DEFAULT_MAX_LINE_LENGTH = CONSTANT_88


RULE_BASIC_FIELDS = {"enabled", "severity", "options"}
