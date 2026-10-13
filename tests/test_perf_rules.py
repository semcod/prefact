"""Unit tests for performance optimizations in rules and helpers."""

import ast
from pathlib import Path
from unittest.mock import patch

import pytest

from prefact.config import Config
from prefact.rules.autoflake_based import AutoflakeHelper
from prefact.rules.import_linter_based import ImportLinterHelper
from prefact.rules.importchecker_based.dependency_analysis import ImportDependencyAnalysis
from prefact.rules.mypy_based import MyPyHelper, ReturnTypeInferrer, SmartReturnTypeRule
from prefact.rules.ruff_based import RuffHelper


def test_ruff_helper_preload_and_cache(tmp_path: Path) -> None:
    """Test RuffHelper.preload_files populates cache properly."""
    f1 = tmp_path / "mod1.py"
    f2 = tmp_path / "mod2.py"
    f1.write_text("import sys\nimport os\n")
    f2.write_text("def hello():\n    return 42\n")

    RuffHelper.clear_cache()
    assert str(f1) not in RuffHelper._CACHE

    RuffHelper.preload_files([f1, f2])
    # Both paths should now be cached
    assert str(f1) in RuffHelper._CACHE or str(f1.resolve()) in RuffHelper._CACHE
    assert str(f2) in RuffHelper._CACHE or str(f2.resolve()) in RuffHelper._CACHE

    # check_file uses cache
    res1 = RuffHelper.check_file(f1, ["F401"])
    assert isinstance(res1, list)


def test_return_type_inferrer_infer_from_node() -> None:
    """Test infer_from_node infers return type without walking entire module."""
    source = """def compute(x):
    if x > 0:
        return 1
    return 0

def other():
    return 'hello'
"""
    tree = ast.parse(source)
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)
    assert func_node.name == "compute"

    inferred = ReturnTypeInferrer.infer_from_node(func_node)
    assert inferred == "int"

    # Nested functions should not pollute outer function return type
    nested_source = """def outer():
    def inner():
        return 123
    return 'outer_str'
"""
    tree_nested = ast.parse(nested_source)
    outer_node = tree_nested.body[0]
    assert isinstance(outer_node, ast.FunctionDef)
    inferred_outer = ReturnTypeInferrer.infer_from_node(outer_node)
    assert inferred_outer == "str"


def test_missing_tools_early_exit(tmp_path: Path) -> None:
    """Test helpers gracefully return empty results when binaries are missing."""
    test_file = tmp_path / "test.py"
    test_file.write_text("x = 1\n")

    with patch.object(AutoflakeHelper, "is_available", return_value=False):
        assert AutoflakeHelper.check_file(test_file) == []
        assert AutoflakeHelper.check_source("x = 1") == []
        assert AutoflakeHelper.fix_file(test_file) is False
        assert AutoflakeHelper.fix_source("x = 1") == "x = 1"

    with patch.object(ImportLinterHelper, "is_available", return_value=False):
        assert ImportLinterHelper.run_linter(test_file) == []
        assert ImportLinterHelper.check_file(test_file, {}) == []

    with patch.object(MyPyHelper, "is_available", return_value=False):
        assert MyPyHelper.check_file(test_file) == []


def test_dependency_analysis_no_false_positive_circular_imports(tmp_path: Path) -> None:
    """Test that importing submodules from same package is not falsely flagged as circular."""
    config = Config(project_root=tmp_path)
    rule = ImportDependencyAnalysis(config)

    file_path = tmp_path / "pkg" / "sub" / "module_a.py"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    source = """from pkg.models import User
from pkg.utils import helper
"""
    # Neither pkg.models nor pkg.utils is pkg.sub.module_a, so no circular import
    issues = rule.scan_file(file_path, source)
    circular_issues = [i for i in issues if "Circular import" in i.message]
    assert len(circular_issues) == 0


def test_config_disables_heavy_rules_by_default() -> None:
    """Test that heavy external-tool rules are disabled by default."""
    cfg = Config()
    for rule_id in (
        "type-checking",
        "unused-variables",
        "import-layers",
        "no-relative-imports",
        "module-independence",
        "custom-architecture",
        "import-dependencies",
        "import-optimization",
        "isorted-imports",
    ):
        assert cfg.rule_enabled(rule_id) is False, f"Rule {rule_id} should be disabled by default"

    # Core AST rules should remain enabled
    assert cfg.rule_enabled("relative-imports") is True
    assert cfg.rule_enabled("magic-numbers") is True
