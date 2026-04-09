import json
import logging
import sys
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from .formatters import JsonFormatter


class LogLevel(str, Enum):
    DEBUG = "DEBUG"; INFO = "INFO"; WARNING = "WARNING"; ERROR = "ERROR"; CRITICAL = "CRITICAL"

class PprefactLogger:
    def __init__(self, name: str = "prefact", level: Union[LogLevel, str] = LogLevel.INFO, format_type: str = "json", output_file: Optional[Path] = None, enable_telemetry: bool = False):
        self.name = name
        self.level = LogLevel(level)
        self.format_type = format_type
        self.output_file = output_file
        self.enable_telemetry = enable_telemetry
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.level.value))
        self.logger.handlers.clear()
        self._setup_handlers()
        self.telemetry_callbacks: list[Callable] = []

    def _setup_handlers(self) -> None:
        formatter = JsonFormatter() if self.format_type == "json" else logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        if self.output_file:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.output_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs) -> None: self._log(LogLevel.DEBUG, message, **kwargs)
    def info(self, message: str, **kwargs) -> None: self._log(LogLevel.INFO, message, **kwargs)
    def warning(self, message: str, **kwargs) -> None: self._log(LogLevel.WARNING, message, **kwargs)
    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        if error: kwargs.update({"error_type": type(error).__name__, "error_message": str(error), "traceback": traceback.format_exc()})
        self._log(LogLevel.ERROR, message, **kwargs)
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        if error: kwargs.update({"error_type": type(error).__name__, "error_message": str(error), "traceback": traceback.format_exc()})
        self._log(LogLevel.CRITICAL, message, **kwargs)

    def _log(self, level: LogLevel, message: str, **kwargs) -> None:
        log_record = {"timestamp": datetime.utcnow().isoformat(), "level": level.value, "logger": self.name, "message": message, **kwargs}
        getattr(self.logger, level.value.lower())(json.dumps(log_record))
        if self.enable_telemetry: self._send_telemetry(log_record)

    def _send_telemetry(self, log_record: Dict[str, Any]) -> None:
        for callback in self.telemetry_callbacks:
            try: callback(log_record)
            except Exception: pass

    def add_telemetry_callback(self, callback: Callable) -> None: self.telemetry_callbacks.append(callback)
    def log_scan_start(self, file_count: int, rule_ids: list[str]) -> None: self.info("scan_started", event_type="scan_start", file_count=file_count, rule_ids=rule_ids)
    def log_scan_complete(self, duration: float, issues_found: int, fixes_applied: int) -> None: self.info("scan_completed", event_type="scan_complete", duration_seconds=duration, issues_found=issues_found, fixes_applied=fixes_applied)
    def log_rule_execution(self, rule_id: str, file_path: Path, duration: float, issues: int) -> None: self.debug("rule_executed", event_type="rule_execution", rule_id=rule_id, file_path=str(file_path), duration_ms=duration * 1000, issues_found=issues)
    def log_plugin_loaded(self, plugin_name: str, version: str) -> None: self.info("plugin_loaded", event_type="plugin_loaded", plugin_name=plugin_name, version=version)
    def log_performance_metrics(self, metrics: Dict[str, Any]) -> None: self.info("performance_metrics", event_type="performance", **metrics)
