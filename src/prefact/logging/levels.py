"""Log level definitions for prefact."""

from enum import Enum


class LogLevel(str, Enum):
    """Log levels for prefact."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
