"""Tests for the dependency checker module."""


import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from prefact.autonomous.dependency_checker import DependencyChecker

pytestmark = [pytest.mark.unit, pytest.mark.deps]


@pytest.fixture
def project_with_pyproject(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["hatchling"]\n\n'
        "[project]\n"
        'name = "demo"\n'
        "dependencies = [\n"
        '    "click>=8.0.0",\n'
        '    "rich>=12.0.0",\n'
        '    "pyyaml>=6.0",\n'
        "]\n"
    )
    return tmp_path


@pytest.fixture
def project_with_requirements(tmp_path: Path) -> Path:
    (tmp_path / "requirements.txt").write_text(
        "click==8.0.0\nrich>=12.0.0\npyyaml\n"
    )
    return tmp_path


@pytest.fixture
def pip_outdated_json() -> str:
    return json.dumps([
        {"name": "click", "version": "8.0.0", "latest_version": "8.2.0", "latest_filetype": "wheel"},
        {"name": "rich", "version": "12.0.0", "latest_version": "13.9.0", "latest_filetype": "wheel"},
        {"name": "unrelated-pkg", "version": "1.0", "latest_version": "2.0", "latest_filetype": "wheel"},
    ])


class TestDependencyChecker:
    def test_parse_pyproject_toml(self, project_with_pyproject: Path) -> None:
        checker = DependencyChecker(project_with_pyproject)
        checker._collect_declared_deps()
        assert "click" in checker.declared_deps
        assert "rich" in checker.declared_deps
        assert "pyyaml" in checker.declared_deps

    def test_parse_requirements_txt(self, project_with_requirements: Path) -> None:
        checker = DependencyChecker(project_with_requirements)
        checker._collect_declared_deps()
        assert "click" in checker.declared_deps
        assert checker.declared_deps["click"] == "==8.0.0"
        assert "rich" in checker.declared_deps
        assert "pyyaml" in checker.declared_deps

    def test_no_dep_files(self, tmp_path: Path) -> None:
        checker = DependencyChecker(tmp_path)
        issues = checker.check_dependencies()
        assert issues == []

    @patch("prefact.autonomous.dependency_checker.subprocess.run")
    def test_outdated_filtering(
        self, mock_run: MagicMock, project_with_pyproject: Path, pip_outdated_json: str
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout=pip_outdated_json, stderr="")
        checker = DependencyChecker(project_with_pyproject)
        issues = checker.check_dependencies()

        # Only click and rich should appear (unrelated-pkg is not declared)
        names = [i["examples"][0]["message"] for i in issues]
        assert any("click" in n for n in names)
        assert any("rich" in n for n in names)
        assert not any("unrelated" in n for n in names)

    @patch("prefact.autonomous.dependency_checker.subprocess.run")
    def test_all_up_to_date(
        self, mock_run: MagicMock, project_with_pyproject: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
        checker = DependencyChecker(project_with_pyproject)
        issues = checker.check_dependencies()
        assert issues == []

    @patch("prefact.autonomous.dependency_checker.subprocess.run")
    def test_issue_group_shape(
        self, mock_run: MagicMock, project_with_pyproject: Path, pip_outdated_json: str
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout=pip_outdated_json, stderr="")
        checker = DependencyChecker(project_with_pyproject)
        issues = checker.check_dependencies()

        for issue in issues:
            assert issue["rule_id"] == "outdated-dependency"
            assert issue["severity"] == "warning"
            assert "examples" in issue
            assert len(issue["examples"]) == 1
            assert "line" in issue["examples"][0]
            assert "message" in issue["examples"][0]

    @patch("prefact.autonomous.dependency_checker.subprocess.run")
    def test_line_number_detection(
        self, mock_run: MagicMock, project_with_pyproject: Path, pip_outdated_json: str
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout=pip_outdated_json, stderr="")
        checker = DependencyChecker(project_with_pyproject)
        issues = checker.check_dependencies()

        # click is on line 6 of pyproject.toml ('    "click>=8.0.0",')
        click_issue = [i for i in issues if "click" in i["examples"][0]["message"]]
        assert click_issue
        assert click_issue[0]["examples"][0]["line"] > 0

    def test_normalize(self) -> None:
        assert DependencyChecker._normalize("PyYAML") == "pyyaml"
        assert DependencyChecker._normalize("ast-decompiler") == "ast_decompiler"
        assert DependencyChecker._normalize("My.Package") == "my_package"

    @patch("prefact.autonomous.dependency_checker.subprocess.run")
    def test_pip_failure_graceful(
        self, mock_run: MagicMock, project_with_pyproject: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        checker = DependencyChecker(project_with_pyproject)
        issues = checker.check_dependencies()
        assert issues == []
