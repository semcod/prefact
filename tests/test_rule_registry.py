"""Regression tests for the rule registry: no rule_id collisions, and
get_all_rules() surfaces every rule actually registered via @register.

Context: multiple backend-specific rule classes (ruff/isort/mypy/pylint/
autoflake/unimport/importchecker-based) used to share a bare rule_id with
their AST-only "canonical" counterpart (e.g. both `SortedImports` and
`ISortedImports` claimed `rule_id = "sorted-imports"`). Since `@register`
just overwrites `_rule_cache[rule_id]`, whichever module `prefact/rules/
__init__.py` happened to import last silently won -- an unlabeled,
import-order-dependent behavior with no user-facing way to choose. Each
backend class now gets its own namespaced rule_id (already anticipated by
`LazyRuleRegistry._rule_modules`'s keys, which existed before this fix but
never matched the classes' actual `rule_id` values); the AST-only canonical
rule keeps an `ast-`-prefixed id of its own for symmetry.

Separately, `get_all_rules()` used to iterate only `_rule_modules`'s keys,
which have several stale/mismatched entries (e.g. `composite-*`/`llm-*`
point at module paths that don't exist), silently hiding ~24 of the ~46
actually-registered rules from scan/fix/validate/CLI output.
"""

from collections import Counter

from prefact.rules import get_all_rules
from prefact.rules.registry import get_lazy_registry


def test_no_rule_id_collisions_in_live_registry() -> None:
    """Every registered rule_id maps to exactly one class."""
    rules = get_all_rules()
    # get_all_rules() itself can't show a collision (dict keys are unique by
    # construction) -- the real regression is upstream import-order
    # overwriting _rule_cache silently. Assert instead that the previously
    # colliding ids now resolve to the intended canonical (ast-*) owner.
    assert rules["ast-sorted-imports"].__name__ == "SortedImports"
    assert rules["isorted-imports"].__name__ == "ISortedImports"
    assert rules["ruff-sorted-imports"].__name__ == "RuffSortedImports"

    assert rules["ast-string-concat"].__name__ == "StringConcatToFstring"
    assert rules["string-concat-fstring"].__name__ == "StringConcatToFString"
    assert rules["pylint-string-concat"].__name__ == "PylintStringConcat"

    assert rules["ast-unused-imports"].__name__ == "UnusedImports"
    assert rules["ruff-unused-imports"].__name__ == "RuffUnusedImports"
    assert rules["autoflake-unused-imports"].__name__ == "AutoflakeUnusedImports"
    assert rules["unimport-unused-imports"].__name__ == "UnimportUnusedImports"
    assert (
        rules["importchecker-unused-imports"].__name__ == "ImportCheckerUnusedImports"
    )


def test_no_duplicate_rule_id_class_attributes_in_source() -> None:
    """No two live (non-backup) rule classes declare the same rule_id string.

    A source-level grep, not just a registry-level check, so this catches a
    reintroduced collision even before anything gets imported/registered.
    """
    import re
    from pathlib import Path

    rules_dir = Path(__file__).parent.parent / "src" / "prefact" / "rules"
    pattern = re.compile(r'rule_id\s*=\s*"([^"]+)"')

    ids: list[str] = []
    for path in rules_dir.rglob("*.py"):
        if path.suffix == ".bak" or ".bak" in path.suffixes:
            continue
        ids.extend(pattern.findall(path.read_text(encoding="utf-8")))

    dupes = {rule_id: count for rule_id, count in Counter(ids).items() if count > 1}
    assert dupes == {}, f"duplicate rule_id assignments found: {dupes}"


def test_get_all_rules_is_not_limited_to_stale_rule_modules_keys() -> None:
    """get_all_rules() must surface rules whose id isn't a _rule_modules key.

    Several classes' actual `rule_id` (e.g. `AutoflakeUnusedVariables`'s
    "unused-variables", `ImportLinterNoRelative`'s "no-relative-imports")
    were never added as keys to the static `_rule_modules` dict at all, so
    relying on that dict alone (the old `get_all_rules()` behavior)
    silently hid them from scan/fix/validate/CLI regardless of any
    collision -- merging in the eagerly-populated `_rule_cache` is what
    surfaces them.
    """
    registry = get_lazy_registry()
    rules = get_all_rules()

    ids_missing_from_static_map = {
        rid for rid in rules if rid not in registry._rule_modules
    }
    assert "unused-variables" in ids_missing_from_static_map
    assert "no-relative-imports" in ids_missing_from_static_map

    # And the total count should reflect (roughly) everything that actually
    # gets registered, not just the ~21 that used to survive the old
    # _rule_modules-only iteration.
    assert len(rules) >= 40
