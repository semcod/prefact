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
                for raw_line in f:
                    gitignore_pattern = raw_line.strip()
                    # Skip empty lines and comments
                    if gitignore_pattern and not gitignore_pattern.startswith("#"):
                        patterns.append(gitignore_pattern)
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


def _dedupe_issues(issues: list[Issue]) -> list[Issue]:
    """Drop issues that repeat an earlier one exactly, preserving order.

    Composite rules wrap the very same rule objects the scanner also registers
    standalone, so a file scanned once yields each finding from both paths —
    identical rule_id, location and message. Reports and generated TODO lists
    consumed those duplicates as separate work items. Deduplicating here covers
    every producer instead of one call site.
    """
    seen: set[tuple[str, str, int, int, str]] = set()
    unique: list[Issue] = []
    for issue in issues:
        issue_key = (issue.rule_id, str(issue.file), issue.line, issue.col, issue.message)
        if issue_key in seen:
            continue
        seen.add(issue_key)
        unique.append(issue)
    return unique


_SKIP_DIRS: frozenset[str] = frozenset({
    ".git",
    "node_modules",
    "__pycache__",
    "env",
    ".env",
    "venv",
    ".venv",
    "virtualenv",
    "site-packages",
    "build",
    "dist",
    "target",
    ".cache",
    "cache",
    ".tmp",
    "tmp",
    ".subactor",
    ".codex",
    "state",
    ".pytest_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".governance",
    "tests",
    ".worktrees",
    "artifacts",
    ".planfile",
    ".benchmarks",
    "benchmarks",
    "bench-results",
    "twinerd-bench-results",
    ".cargo",
    "c2004",
    "c2004-git-backup",
    "workshop",
    "managed_components",
    "vendor",
    "maskservice.local",
})


def _resolve_rel_path(path: Path, root: Path) -> Path | None:
    """Resolve path relative to root, returning None if not under root."""
    if not path.is_absolute():
        return path
    try:
        return path.relative_to(root)
    except ValueError:
        try:
            return path.resolve().relative_to(root)
        except ValueError:
            return None


def _matches_pattern_direct(path_str: str, pat: str) -> bool:
    return fnmatch.fnmatch(path_str, pat) or fnmatch.fnmatch(path_str, f"*/{pat}")


def _matches_directory_pattern(rel: Path, rel_str: str, pat: str) -> bool:
    clean_pat = pat.strip("/*")
    if not clean_pat:
        return False
    return (
        clean_pat in rel.parts
        or fnmatch.fnmatch(rel_str, f"*/{clean_pat}/*")
        or fnmatch.fnmatch(rel_str, f"{clean_pat}/*")
    )


def _matches_parent_pattern(rel: Path, pat: str) -> bool:
    for parent in rel.parents:
        parent_str = str(parent)
        if parent_str != "." and _matches_pattern_direct(parent_str, pat):
            return True
    return False


def _matches_exclude_pattern(rel: Path, rel_str: str, pat: str) -> bool:
    if not pat:
        return False
    return (
        _matches_pattern_direct(rel_str, pat)
        or _matches_directory_pattern(rel, rel_str, pat)
        or _matches_parent_pattern(rel, pat)
    )


def _has_skip_dir(rel: Path) -> bool:
    return any(part in _SKIP_DIRS or part.endswith(".local") for part in rel.parts)


def _matches_any_pattern(rel: Path, patterns: list[str]) -> bool:
    rel_str = str(rel)
    return any(
        _matches_exclude_pattern(rel, rel_str, pat)
        for pat in patterns
    )


def _is_path_excluded(
    path: Path,
    root: Path,
    exclude_patterns: list[str],
    rel: Path | None = None,
) -> bool:
    target_rel = rel if rel is not None else _resolve_rel_path(path, root)
    if target_rel is None or _has_skip_dir(target_rel):
        return True
    return _matches_any_pattern(target_rel, exclude_patterns)


class Scanner:
    """Discovers Python files and runs all enabled rules against them."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._rules: list[BaseRule] = []
        self._project_root = self.config.project_root.resolve()
        # Load gitignore patterns
        self._gitignore_patterns = _load_gitignore(config.project_root)
        # Combine with config exclude patterns
        exclude_list = config.exclude or []
        self._exclude_patterns = [*exclude_list, *self._gitignore_patterns]
        for rule_id, rule_cls in get_all_rules().items():
            if config.rule_enabled(rule_id):
                self._rules.append(rule_cls(config))

    def collect_files(self) -> list[Path]:
        """Walk the project tree collecting files that match an include pattern.

        Uses os.walk with topdown pruning so excluded directories (venv,
        node_modules, ...) are skipped before descending into them, instead
        of the previous root.glob() approach which fully traversed the tree
        (stat'ing every file inside a populated virtualenv) before filtering.
        """
        root = self._project_root
        include_patterns = self.config.include or []
        files: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            # 1. Fast O(1) prune by directory basename
            dirnames[:] = [
                d for d in dirnames
                if d not in _SKIP_DIRS and not d.endswith(".local")
            ]

            # 2. Path-based exclude pruning for remaining directories
            current_dir = Path(dirpath)
            try:
                rel_dir = current_dir.relative_to(root)
            except ValueError:
                rel_dir = current_dir.resolve().relative_to(root)

            dirnames[:] = [
                d for d in dirnames
                if not self._excluded(current_dir / d, rel=rel_dir / d)
            ]

            # 3. For files, check include patterns first before expensive exclude check
            rel_dir_str = str(rel_dir)
            for filename in filenames:
                rel_str = f"{rel_dir_str}/{filename}" if rel_dir_str != "." else filename
                if include_patterns and not any(
                    _match_gitignore_pattern(rel_str, pattern)
                    for pattern in include_patterns
                ):
                    continue

                file_path = current_dir / filename
                rel_path = rel_dir / filename if rel_dir_str != "." else Path(filename)
                if self._excluded(file_path, rel=rel_path):
                    continue
                files.append(file_path)
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
        if any(getattr(r, "rule_id", "").startswith("ruff-") for r in self._rules):
            try:
                from prefact.rules.ruff_based import RuffHelper

                RuffHelper.preload_files(list(sources.keys()))
            except Exception:
                pass

        results: dict[Path, list[Issue]] = {}
        for path, source in sources.items():
            file_issues: list[Issue] = []
            for rule in self._rules:
                file_issues.extend(rule.scan_file(path, source))
            file_issues = _dedupe_issues(file_issues)
            if file_issues:
                results[path] = file_issues
        return results

    def _excluded(self, path: Path, rel: Path | None = None) -> bool:
        """Check if a path should be excluded based on patterns."""
        return _is_path_excluded(
            path,
            self._project_root,
            self._exclude_patterns,
            rel=rel,
        )
