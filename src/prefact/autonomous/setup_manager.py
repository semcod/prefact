"""Setup management for autonomous prefact - configuration and examples."""

import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict

import yaml
from rich.progress import Progress

from prefact.config_extended import ConfigGenerator

from ._base import BaseManager, console


# Standard environment, cache, session and dependency directories to skip
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", "env", ".env", "venv", ".venv",
    "virtualenv", "site-packages", "build", "dist", "target", ".cache",
    "cache", ".tmp", "tmp", ".subactor", ".codex", "state", ".pytest_cache",
    ".ruff_cache", ".idea", ".vscode", ".governance", ".worktrees",
    "artifacts", ".planfile", ".benchmarks", "htmlcov", "sessions", ".sessions",
}

AI_INDICATORS = ("TODO", "placeholder", "AI", "LLM")


def _file_contains_ai_markers(py_file: Path) -> bool:
    """Check if a Python file contains AI-related indicators."""
    try:
        file_text = py_file.read_text(encoding="utf-8", errors="ignore")
        return any(indicator in file_text for indicator in AI_INDICATORS)
    except Exception:
        return False


class SetupManager(BaseManager):
    """Handles project setup - configuration and examples."""

    def create_refact_config(self) -> None:
        """Create prefact.yaml configuration automatically."""
        # Detect project type and characteristics
        project_info = self.detect_project_info()

        # Generate configuration
        config_content = ConfigGenerator.generate_extended_config(
            self.project_root,
            tools=["ruff", "mypy", "isort"],
            rules=["unused-imports", "relative-imports", "missing-return-type"],
        )

        # Customize based on project
        generated_config = yaml.safe_load(config_content)

        # Add project-specific settings
        generated_config["project_root"] = str(self.project_root)
        generated_config["package_name"] = project_info["package_name"]

        # Enable LLM rules if AI-generated code detected
        if project_info["has_ai_code"]:
            generated_config["rules"]["llm-hallucinations"] = {"enabled": True}
            generated_config["rules"]["magic-numbers"] = {"enabled": True}

        # Write configuration
        with open(self.refact_config_path, "w") as f:
            yaml.dump(
                generated_config, f, default_flow_style=False, sort_keys=False
            )

        console.print(f"✅ Created {self.refact_config_path}")

    def _detect_ai_code(self) -> bool:
        """Check for AI indicators (bounded to top-level source files, max 50 files)."""
        checked_count = 0
        for dirpath, dirnames, filenames in os.walk(self.project_root, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
            for filename in filenames:
                if filename.endswith(".py"):
                    if _file_contains_ai_markers(Path(dirpath) / filename):
                        return True
                    checked_count += 1
                    if checked_count >= 50:
                        return False
        return False

    def _detect_has_tests(self) -> bool:
        """Check for tests (shallow checks first, then bounded directory presence)."""
        if (self.project_root / "tests").exists() or (self.project_root / "test").exists():
            return True
        for item in self.project_root.iterdir():
            if item.name not in SKIP_DIRS and "test" in item.name.lower():
                return True
        return False

    def _is_test_project(self) -> bool:
        """Check if this is a test project."""
        name = self.project_root.name.lower()
        return "test" in name or "example" in name

    def detect_project_info(self) -> Dict[str, Any]:
        """Detect project characteristics."""
        return {
            "package_name": self.project_root.name,
            "has_ai_code": self._detect_ai_code(),
            "is_test_project": self._is_test_project(),
            "has_tests": self._detect_has_tests(),
            "python_version": "3.8",
        }

    def run_examples(self) -> bool:
        """Run all examples and verify they work."""
        if not self.examples_dir.exists():
            console.print("⚠️ No examples directory found", style="yellow")
            return True

        # Find all prefact.yaml files in examples
        example_configs = list(self.examples_dir.rglob("prefact.yaml"))

        if not example_configs:
            console.print("⚠️ No example configurations found", style="yellow")
            return True

        all_examples_passed = True

        with Progress() as progress:
            task = progress.add_task("Running examples...", total=len(example_configs))

            for config_path in example_configs:
                example_dir = config_path.parent

                try:
                    # Run prefact scan
                    scan_process = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "prefact.cli",
                            "scan",
                            "--path",
                            str(example_dir),
                            "--config",
                            str(config_path),
                        ],
                        capture_output=True,
                        text=True,
                        cwd=self.project_root,
                    )

                    if scan_process.returncode != 0:
                        console.print(
                            f"❌ Example {example_dir.name} failed: {scan_process.stderr}",
                            style="red",
                        )
                        all_examples_passed = False
                    else:
                        console.print(f"✅ Example {example_dir.name} passed")

                except Exception as e:
                    console.print(
                        f"❌ Error running example {example_dir.name}: {e}", style="red"
                    )
                    all_examples_passed = False

                progress.advance(task)

        return all_examples_passed
