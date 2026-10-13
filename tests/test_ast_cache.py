"""Unit tests for AST caching across rules."""

import ast
from prefact.rules import BaseRule, clear_ast_cache, parse_cached


def test_parse_cached_returns_same_ast_instance():
    clear_ast_cache()
    source = "def foo(): return 42"
    tree1 = parse_cached(source)
    tree2 = parse_cached(source)
    assert tree1 is not None
    assert tree2 is not None
    assert tree1 is tree2


def test_parse_cached_handles_syntax_error():
    clear_ast_cache()
    bad_source = "def bad(:"
    assert parse_cached(bad_source) is None


def test_base_rule_parse_ast():
    clear_ast_cache()
    source = "x = [1, 2, 3]"
    tree = BaseRule.parse_ast(source)
    assert isinstance(tree, ast.Module)
    assert BaseRule.parse_ast(source) is tree
