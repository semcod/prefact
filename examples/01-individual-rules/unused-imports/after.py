"""Example file with unused imports removed."""

from typing import Any

from data_helpers import DataProcessor, format_timestamp, process_data, read_file


def build_summary(filepath: str) -> dict[str, Any]:
    """Summarize a file using the shared data helpers."""
    processor = DataProcessor()
    for key, item_length in process_data(read_file(filepath).splitlines()).items():
        processor.add_data(key, item_length)
    return {
        "entries": processor.data,
        "generated_at": format_timestamp(processor.timestamp),
    }
