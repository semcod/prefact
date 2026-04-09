"""Dependency freshness checker for autonomous prefact.

Detects outdated Python dependencies by:
1. Parsing pyproject.toml / requirements.txt for declared dependencies
2. Running `pip list --outdated --format=json` to find stale packages
3. Producing issue dicts compatible with TodoManager
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from prefact.autonomous._base import BaseManager, console


# Regex for requirements.txt lines: package==version or package>=version etc.
_REQ_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_][A-Za-z0-9._-]*)\s*"
    r"(?:(?P<op>[><=!~]+)\s*(?P<ver>[^\s,;#]+))?"
)


class DependencyChecker(BaseManager):
    """Checks for outdated project dependencies."""

    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.declared_deps: Dict[str, str] = {}  # name -> version_spec
        self.outdated: List[Dict[str, Any]] = []  # pip list --outdated rows

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_dependencies(self) -> List[Dict[str, Any]]:
        """Run full dependency check and return issue groups for TodoManager.

        Each returned dict has the same shape as ProjectScanner.group_issues():
            {
                "rule_id": "outdated-dependency",
                "file": "<source file>",
                "count": 1,
                "severity": "warning",
                "examples": [{"line": 0, "message": "..."}],
            }
        """
        self._collect_declared_deps()

        if not self.declared_deps:
            console.print("ℹ️  No dependency files found – skipping dependency check")
            return []

        self._query_pip_outdated()

        if not self.outdated:
            console.print("✅ All dependencies are up-to-date")
            return []

        issues = self._build_issue_groups()
        console.print(
            f"📦 Found {len(issues)} outdated dependenc{'y' if len(issues) == 1 else 'ies'}"
        )
        return issues

    # ------------------------------------------------------------------
    # Collect declared dependencies
    # ------------------------------------------------------------------

    def _collect_declared_deps(self) -> None:
        """Gather dependency names from pyproject.toml and requirements*.txt."""
        self.declared_deps = {}
        self._parse_pyproject_toml()
        self._parse_requirements_files()

    def _parse_pyproject_toml(self) -> None:
        """Extract dependencies from pyproject.toml [project].dependencies."""
        pyproject = self.project_root / "pyproject.toml"
        if not pyproject.exists():
            return

        try:
            # Use tomli for Python < 3.11, tomllib for 3.11+
            try:
                import tomllib  # Python 3.11+
            except ModuleNotFoundError:
                import tomli as tomllib  # type: ignore[no-redef]

            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            deps = data.get("project", {}).get("dependencies", [])
            for dep_str in deps:
                name, spec = self._parse_dep_string(dep_str)
                if name:
                    self.declared_deps[self._normalize(name)] = spec
        except Exception as exc:
            console.print(f"⚠️  Could not parse pyproject.toml: {exc}")

    def _parse_requirements_files(self) -> None:
        """Parse requirements.txt / requirements*.txt files."""
        for req_file in sorted(self.project_root.glob("requirements*.txt")):
            try:
                for raw_line in req_file.read_text(encoding="utf-8").splitlines():
                    line = raw_line.strip()
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue
                    m = _REQ_RE.match(line)
                    if m:
                        name = m.group("name")
                        op = m.group("op") or ""
                        ver = m.group("ver") or ""
                        self.declared_deps[self._normalize(name)] = f"{op}{ver}"
            except Exception as exc:
                console.print(f"⚠️  Could not parse {req_file.name}: {exc}")

    # ------------------------------------------------------------------
    # Query pip for outdated packages
    # ------------------------------------------------------------------

    def _query_pip_outdated(self) -> None:
        """Run ``pip list --outdated`` and keep only declared deps."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.project_root,
            )
            if result.returncode != 0:
                console.print(f"⚠️  pip list --outdated failed: {result.stderr.strip()}")
                self.outdated = []
                return

            all_outdated = json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            console.print("⚠️  pip list --outdated timed out (120 s)")
            self.outdated = []
            return
        except Exception as exc:
            console.print(f"⚠️  Could not run pip list --outdated: {exc}")
            self.outdated = []
            return

        # Keep only packages that are declared in the project
        declared_norm = set(self.declared_deps.keys())
        self.outdated = [
            pkg
            for pkg in all_outdated
            if self._normalize(pkg.get("name", "")) in declared_norm
        ]

    # ------------------------------------------------------------------
    # Build issue groups for TodoManager
    # ------------------------------------------------------------------

    def _build_issue_groups(self) -> List[Dict[str, Any]]:
        """Convert outdated list into TodoManager-compatible issue groups."""
        # Determine which source file to attribute the issue to
        source_file = self._find_dep_source_file()
        issues: List[Dict[str, Any]] = []

        for pkg in self.outdated:
            name = pkg.get("name", "unknown")
            current = pkg.get("version", "?")
            latest = pkg.get("latest_version", "?")
            latest_type = pkg.get("latest_filetype", "")

            msg = (
                f"Outdated dependency: {name} {current} → {latest}"
                f"{' (' + latest_type + ')' if latest_type else ''}"
            )

            line_no = self._find_dep_line(source_file, name)

            issues.append(
                {
                    "rule_id": "outdated-dependency",
                    "file": str(source_file),
                    "count": 1,
                    "severity": "warning",
                    "examples": [{"line": line_no, "message": msg}],
                }
            )

        return issues

    def _find_dep_source_file(self) -> Path:
        """Return the most relevant dependency file path."""
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            return pyproject

        for req in sorted(self.project_root.glob("requirements*.txt")):
            return req

        return self.project_root / "pyproject.toml"

    def _find_dep_line(self, source_file: Path, package_name: str) -> int:
        """Try to locate the line number of *package_name* in *source_file*."""
        if not source_file.exists():
            return 0

        try:
            norm = self._normalize(package_name)
            for i, line in enumerate(
                source_file.read_text(encoding="utf-8").splitlines(), start=1
            ):
                # Match various forms: "click>=8.0", "click", 'click'
                if norm in self._normalize(line):
                    return i
        except Exception:
            pass
        return 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(name: str) -> str:
        """PEP 503 normalisation: lowercase, hyphens → underscores."""
        return re.sub(r"[-_.]+", "_", name).lower()

    @staticmethod
    def _parse_dep_string(dep: str) -> Tuple[str, str]:
        """Parse ``'click>=8.0.0'`` → ``('click', '>=8.0.0')``."""
        dep = dep.strip()
        # Remove environment markers  (e.g. ; python_version<'3.11')
        dep = dep.split(";")[0].strip()
        m = _REQ_RE.match(dep)
        if m:
            name = m.group("name")
            op = m.group("op") or ""
            ver = m.group("ver") or ""
            return name, f"{op}{ver}"
        return "", ""
