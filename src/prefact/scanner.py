"""Scanner – walks the project tree and collects issues."""

import fnmatch
import os
from pathlib import Path

from prefact.config import Config
from prefact.models import Issue
from prefact.rules import BaseRule, get_all_rules


def _load_gitignore(root: Path) -> list[str]:
    """Load .gitignore patterns from project root."""
    gitignore_path = root / ".gitignore"
    patterns = []
    if gitignore_path.exists():
        try:
            with open(gitignore_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except (OSError, UnicodeDecodeError):
            pass
    return patterns


def _match_gitignore_pattern(path: str, pattern: str) -> bool:
    """Match a path against a gitignore-style pattern."""
    # Handle directory-only patterns (ending with /)
    if pattern.endswith("/"):
        pattern = pattern.rstrip("/")
        if not path.endswith("/"):
            path = f"{path}/"

    # Handle negation patterns (starting with !)
    if pattern.startswith("!"):
        return False  # Negation handled separately

    # Convert pattern to fnmatch format
    # ** matches any number of directories
    if "**" in pattern:
        # Split path and pattern
        path_parts = path.split("/")
        pattern_parts = pattern.split("/")

        # Handle ** at start
        if pattern_parts[0] == "**":
            # Match remaining pattern anywhere in path
            remaining = "/".join(pattern_parts[1:])
            # Try matching at each position
            for i in range(len(path_parts)):
                subpath = "/".join(path_parts[i:])
                if fnmatch.fnmatch(subpath, remaining):
                    return True
            return fnmatch.fnmatch(path, remaining)
        else:
            # Standard fnmatch for simple patterns
            return fnmatch.fnmatch(path, pattern)
    else:
        # Standard fnmatch for simple patterns
        # Also check if pattern matches any path component
        if fnmatch.fnmatch(path, pattern):
            return True
        # Check if pattern matches the basename
        if fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
        # Check if pattern with **/ prefix matches
        if fnmatch.fnmatch(path, f"*/{pattern}") or fnmatch.fnmatch(
            path, f"**/{pattern}"
        ):
            return True
        return False


class Scanner:
    """Discovers Python files and runs all enabled rules against them."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._rules: list[BaseRule] = []
        # Load gitignore patterns
        self._gitignore_patterns = _load_gitignore(config.project_root)
        # Combine with config exclude patterns
        exclude_list = config.exclude or []
        self._exclude_patterns = [*exclude_list, *self._gitignore_patterns]
        for rule_id, rule_cls in get_all_rules().items():
            if config.rule_enabled(rule_id):
                self._rules.append(rule_cls(config))

    def collect_files(self) -> list[Path]:
        root = self.config.project_root.resolve()
        files: list[Path] = []
        for pattern in self.config.include or []:
            # Path.glob already handles ** patterns
            for p in root.glob(pattern):
                if p.is_file() and not self._excluded(p):
                    files.append(p)
        return sorted(set(files))

    def scan(self, files: list[Path] | None = None) -> dict[Path, list[Issue]]:
        if files is None:
            files = self.collect_files()
        # For backward compatibility, load sources if not provided
        sources = {}
        for path in files:
            try:
                source = path.read_text(encoding="utf-8")
                sources[path] = source
            except (OSError, UnicodeDecodeError):
                continue
        return self.scan_sources(sources)

    def scan_sources(self, sources: dict[Path, str]) -> dict[Path, list[Issue]]:
        """Scan files using preloaded sources to avoid I/O operations."""
        results: dict[Path, list[Issue]] = {}
        for path, source in sources.items():
            file_issues: list[Issue] = []
            for rule in self._rules:
                file_issues.extend(rule.scan_file(path, source))
            if file_issues:
                results[path] = file_issues
        return results

    def _excluded(self, path: Path) -> bool:
        """Check if a path should be excluded based on patterns."""
        try:
            root = self.config.project_root.resolve()
            abs_path = path.resolve()
            rel = abs_path.relative_to(root)
            rel_str = str(rel)
        except ValueError:
            # Not under project root, skip
            return True

        import fnmatch

        for pat in self._exclude_patterns:
            if not pat:
                continue

            # Match directly
            if fnmatch.fnmatch(rel_str, pat) or fnmatch.fnmatch(rel_str, f"*/{pat}"):
                return True

            # Match parents
            for parent in rel.parents:
                parent_str = str(parent)
                if parent_str == ".":
                    continue
                if fnmatch.fnmatch(parent_str, pat) or fnmatch.fnmatch(
                    parent_str, f"*/{pat}"
                ):
                    return True

        # Hardcoded safety for common folders if not caught by patterns
        _skip_dirs = {".git", "node_modules", "__pycache__", "env"}
        if any(
            part in _skip_dirs
            or part.startswith(".venv")
            or part.startswith("venv")
            for part in abs_path.parts
        ):
            return True

        return False
