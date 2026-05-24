"""Tests for configuration loading and auto-detection."""

from pathlib import Path

import pytest

from prefact.config import Config
from prefact.defaults import DEFAULT_EXCLUDE, DEFAULT_INCLUDE


@pytest.fixture
def project_with_pyproject(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-cool-app"\n')
    pkg = tmp_path / "src" / "my_cool_app"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    return tmp_path


class TestConfig:
    def test_detect_from_pyproject(self, project_with_pyproject: Path) -> None:
        cfg = Config(project_root=project_with_pyproject)
        name = cfg.detect_package_name()
        assert name == "my_cool_app"

    def test_detect_from_src_layout(self, tmp_path: Path) -> None:
        pkg = tmp_path / "src" / "foobar"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        cfg = Config(project_root=tmp_path)
        assert cfg.detect_package_name() == "foobar"

    def test_detect_top_level_package(self, tmp_path: Path) -> None:
        pkg = tmp_path / "mylib"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        cfg = Config(project_root=tmp_path)
        assert cfg.detect_package_name() == "mylib"

    def test_from_yaml(self, tmp_path: Path) -> None:
        yaml_content = """\
package_name: myapp
rules:
  relative-imports:
    enabled: true
    severity: error
  unused-imports: false
"""
        cfg_path = tmp_path / "prefact.yaml"
        cfg_path.write_text(yaml_content)
        cfg = Config.from_yaml(cfg_path)
        assert cfg.package_name == "myapp"
        assert cfg.rule_enabled("relative-imports") is True
        assert cfg.rule_enabled("unused-imports") is False

    def test_rule_defaults(self) -> None:
        cfg = Config()
        # All rules enabled by default
        assert cfg.rule_enabled("relative-imports") is True
        assert cfg.rule_enabled("nonexistent-rule") is True
        assert cfg.rule_options("nonexistent") == {}

    def test_config_uses_defaults_include(self) -> None:
        cfg = Config()
        assert cfg.include == DEFAULT_INCLUDE

    def test_config_uses_defaults_exclude(self) -> None:
        cfg = Config()
        assert cfg.exclude == DEFAULT_EXCLUDE

    def test_venv_variants_in_defaults(self) -> None:
        for pattern in ("**/.venv/**", "**/.venv*/**", "**/venv/**", "**/venv*/**", "**/env/**"):
            assert pattern in DEFAULT_EXCLUDE, f"Missing pattern: {pattern}"

    def test_scanner_excludes_venv_test(self, tmp_path: Path) -> None:
        from prefact.scanner import Scanner

        venv_dir = tmp_path / ".venv_test" / "lib"
        venv_dir.mkdir(parents=True)
        (venv_dir / "foo.py").write_text("x = 1\n")
        (tmp_path / "main.py").write_text("x = 1\n")

        cfg = Config(project_root=tmp_path)
        scanner = Scanner(cfg)
        files = scanner.collect_files()
        names = [f.name for f in files]
        assert "main.py" in names
        assert "foo.py" not in names, ".venv_test should be excluded"

    def test_config_extended_constants_reexport(self) -> None:
        from prefact.config_extended.constants import DEFAULT_EXCLUDE as CE_EXCLUDE
        from prefact.config_extended.constants import DEFAULT_INCLUDE as CE_INCLUDE

        assert CE_EXCLUDE is DEFAULT_EXCLUDE
        assert CE_INCLUDE is DEFAULT_INCLUDE
