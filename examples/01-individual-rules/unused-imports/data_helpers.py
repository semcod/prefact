"""Shared code for the unused-imports before/after example.

The ``DataProcessor`` class and its helper functions live here so that
``before.py`` and ``after.py`` differ only in their import block instead of
duplicating the same class in both files (PLF-092).
"""

import datetime
from typing import Any


def process_data(data: list[str]) -> dict[str, Any]:
    """Process some data."""
    item_map = {}
    for item in data:
        key = item.lower()
        item_length = len(item)
        item_map[key] = item_length
    return item_map


def format_timestamp(ts: datetime.datetime) -> str:
    """Format a timestamp."""
    return ts.isoformat(sep=" ", timespec="seconds")


def read_file(filepath: str) -> str:
    """Read file contents."""
    with open(filepath) as f:
        return f.read()


class DataProcessor:
    """A class that collects keyed data with a creation timestamp."""

    def __init__(self):
        self.data = {}
        self.timestamp = datetime.datetime.now()

    def add_data(self, key: str, value: Any) -> None:
        """Add data to processor."""
        self.data[key] = value

    def get_data(self, key: str) -> Any:
        """Get data from processor."""
        return self.data.get(key)
