"""Tests for PprefactLogger error-context handling (PLF-037)."""

import pytest

from prefact.logging import PprefactLogger
from prefact.logging.levels import LogLevel


@pytest.fixture
def records():
    captured = []

    logger = PprefactLogger(name="prefact-test-error-context", enable_telemetry=True)
    logger.add_telemetry_callback(captured.append)
    logger.logger.handlers.clear()

    class _Capture:
        def __init__(self):
            self.captured = captured
            self.logger = logger

    return _Capture()


def test_error_with_exception_adds_error_context(records):
    logger = records.logger
    try:
        raise ValueError("boom")
    except ValueError as exc:
        logger.error("scan failed", error=exc)

    assert len(records.captured) == 1
    record = records.captured[0]
    assert record["level"] == LogLevel.ERROR.value
    assert record["message"] == "scan failed"
    assert record["error_type"] == "ValueError"
    assert record["error_message"] == "boom"
    assert "ValueError" in record["traceback"]
    assert "boom" in record["traceback"]


def test_critical_with_exception_adds_error_context(records):
    logger = records.logger
    try:
        raise RuntimeError("fatal")
    except RuntimeError as exc:
        logger.critical("engine crashed", error=exc)

    assert len(records.captured) == 1
    record = records.captured[0]
    assert record["level"] == LogLevel.CRITICAL.value
    assert record["error_type"] == "RuntimeError"
    assert record["error_message"] == "fatal"
    assert "RuntimeError" in record["traceback"]


def test_error_without_exception_has_no_error_context(records):
    records.logger.error("plain failure")
    record = records.captured[0]
    assert record["level"] == LogLevel.ERROR.value
    assert "error_type" not in record
    assert "error_message" not in record
    assert "traceback" not in record


def test_error_context_preserves_extra_kwargs(records):
    logger = records.logger
    try:
        raise OSError("missing")
    except OSError as exc:
        logger.error("io failure", error=exc, file_path="x.py", rule_id="R1")

    record = records.captured[0]
    assert record["file_path"] == "x.py"
    assert record["rule_id"] == "R1"
    assert record["error_type"] == "OSError"
