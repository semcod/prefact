"""Test to strictly enforce version parity across all carriers and package code."""

from __future__ import annotations

import re
from pathlib import Path

import prefact


def test_package_version_is_valid_semver():
    """__version__ must be a valid semver string and not 'unknown'."""
    assert prefact.__version__ != "unknown"
    assert re.match(r"^\d+\.\d+\.\d+", prefact.__version__), f"Invalid version format: {prefact.__version__}"


def test_version_carrier_parity():
    """VERSION file and prefact.__version__ must match strictly."""
    root = Path(__file__).resolve().parent.parent
    version_file = root / "VERSION"
    assert version_file.is_file(), "VERSION file is missing"
    expected_version = version_file.read_text(encoding="utf-8").strip()

    # 1. Check prefact.__version__
    assert prefact.__version__ == expected_version, (
        f"prefact.__version__ ({prefact.__version__}) does not match VERSION ({expected_version})"
    )
