"""Helper class for importchecker operations."""

import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional


class ImportCheckerHelper:
    """Helper class for importchecker operations."""

    @staticmethod
    def check_file(file_path: Path) -> List[Dict]:
        """Check a file using importchecker."""
        try:
            # Import importchecker dynamically
            import importchecker

            # Get module name from file path
            module_name = ImportCheckerHelper._get_module_name(file_path)

            if not module_name:
                return []

            # Run importchecker
            checker = importchecker.ImportChecker(module_name)
            unused_imports = checker.do_importcheck()

            # Convert to issues
            issues = []
            for imp in unused_imports:
                issues.append(
                    {"type": "unused_import", "import": str(imp), "module": module_name}
                )

            return issues
        except ImportError:
            # importchecker not available
            return []
        except Exception:
            return []

    @staticmethod
    def _get_module_name(file_path: Path) -> Optional[str]:
        """Convert file path to module name."""
        # This is simplified - real implementation would need
        # to consider PYTHONPATH and package structure
        path_segments = file_path.with_suffix("").parts

        # Remove common parent directories
        if "src" in path_segments:
            path_segments = path_segments[path_segments.index("src") + 1 :]
        elif "lib" in path_segments:
            path_segments = path_segments[path_segments.index("lib") + 1 :]

        return ".".join(path_segments)

    @staticmethod
    def check_source(source: str, module_name: str = "temp_module") -> List[Dict]:
        """Check source code using importchecker."""
        # Create a temporary module
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / f"{module_name}.py"
            module_path.write_text(source)

            # Add to sys.path temporarily
            sys.path.insert(0, tmpdir)
            try:
                return ImportCheckerHelper.check_file(module_path)
            finally:
                sys.path.remove(tmpdir)
