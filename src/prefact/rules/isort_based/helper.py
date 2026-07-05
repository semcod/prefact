"""ISort helper utilities shared by the isort-based rules."""

from pathlib import Path
from typing import Dict, List, Optional

from prefact.config_extended import DEFAULT_MAX_LINE_LENGTH

try:
    import isort

    HAS_ISORT = True
except ImportError:
    HAS_ISORT = False
    isort = None


class ISortHelper:
    """Helper class for ISort operations."""

    @staticmethod
    def check_file(file_path: Path, config: Optional[Dict] = None) -> List[Dict]:
        """Check if imports in a file are properly sorted."""
        try:
            source = file_path.read_text(encoding="utf-8")
            return ISortHelper.check_source(source, config)
        except Exception:
            return []

    @staticmethod
    def check_source(source: str, config: Optional[Dict] = None) -> List[Dict]:
        """Check if imports in source code are properly sorted."""
        # Default ISort configuration
        isort_config = {
            "profile": "black",
            "multi_line_output": 3,
            "line_length": DEFAULT_MAX_LINE_LENGTH,
            "known_first_party": ["prefact"],
        }

        if config:
            isort_config.update(config)

        # Check if code is sorted
        if not isort.check_code(source, **isort_config):
            # Find specific issues
            issues = []

            # Parse imports to find unsorted sections
            lines = source.splitlines()
            import_blocks = ISortHelper._find_import_blocks(lines)

            for block in import_blocks:
                if not ISortHelper._is_block_sorted(block, isort_config):
                    issues.append(
                        {
                            "line": str(block["start_line"] + 1),
                            "message": f"Import block not properly sorted (lines {block['start_line'] + 1}-{block['end_line'] + 1})",
                            "type": "unsorted_imports",
                        }
                    )

            # Check for missing section separators
            if ISortHelper._needs_section_separators(source, isort_config):
                issues.append(
                    {
                        "line": 1,
                        "message": "Import sections should be separated by blank lines",
                        "type": "missing_separator",
                    }
                )

            return issues

        return []

    @staticmethod
    def _find_import_blocks(lines: List[str]) -> List[Dict]:
        """Find import blocks in the source code."""
        blocks = []
        in_block = False
        start_line = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith(("import ", "from ")):
                if not in_block:
                    in_block = True
                    start_line = i
            elif (
                in_block
                and not stripped
                and not any(
                    lines[j].strip().startswith(("import ", "from "))
                    for j in range(i + 1, min(i + 3, len(lines)))
                )
            ):
                # End of import block
                blocks.append(
                    {
                        "start_line": start_line,
                        "end_line": i - 1,
                        "lines": lines[start_line:i],
                    }
                )
                in_block = False

        # Handle block at end of file
        if in_block:
            blocks.append(
                {
                    "start_line": start_line,
                    "end_line": len(lines) - 1,
                    "lines": lines[start_line:],
                }
            )

        return blocks

    @staticmethod
    def _is_block_sorted(block: Dict, config: Dict) -> bool:
        """Check if an import block is properly sorted."""
        # Use ISort to sort the block and compare
        block_source = "\n".join(block["lines"])
        sorted_source = isort.code(block_source, **config)
        return block_source == sorted_source

    @staticmethod
    def _needs_section_separators(source: str, config: Dict) -> bool:
        """Check if import sections need blank line separators."""
        sorted = isort.code(source, **config)
        # If ISort adds blank lines, they were missing
        return len(sorted.splitlines()) > len(source.splitlines())

    @staticmethod
    def fix_file(file_path: Path, config: Optional[Dict] = None) -> bool:
        """Sort imports in a file using ISort."""
        try:
            source = file_path.read_text(encoding="utf-8")
            fixed_source = ISortHelper.fix_source(source, config)

            if fixed_source != source:
                file_path.write_text(fixed_source, encoding="utf-8")
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def fix_source(source: str, config: Optional[Dict] = None) -> str:
        """Sort imports in source code using ISort."""
        isort_config = {
            "profile": "black",
            "multi_line_output": 3,
            "line_length": DEFAULT_MAX_LINE_LENGTH,
            "known_first_party": ["prefact"],
        }

        if config:
            isort_config.update(config)

        return isort.code(source, **isort_config)
