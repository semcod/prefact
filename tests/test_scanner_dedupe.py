"""Regression tests: one defect reported once, and a disabled rule stays quiet.

Context: composite rules instantiate the very same rule objects the scanner
also registers standalone (`CompositeImportRules` wraps, among others,
`RelativeToAbsoluteImports`), so scanning a file once produced every finding
twice -- identical rule_id, location and message, because each sub-tool
reports under its own id rather than the composite's. Downstream consumers
that turn issues into work items (the autonomous TODO writer) treated the
copies as separate tasks, and a generated TODO listed the same defect twice.

Separately, the composites gated their sub-tools on defect-class names
("unused-imports", "relative-imports") rather than rule ids. `rule_enabled`
returns True for any id it does not know, so those guards never excluded
anything: a rule disabled in prefact.yaml still ran and still reported from
inside a composite.
"""

from pathlib import Path

from prefact.config import Config, RuleConfig
from prefact.rules.composite_rules import CompositeImportRules
from prefact.scanner import Scanner

SOURCE = """\
from __future__ import annotations

from .config import load_config
from .engine import Engine


def main() -> int:
    print(load_config, Engine)
    return 0
"""


def _write(tmp_path: Path) -> Path:
    pkg = tmp_path / "myapp"
    pkg.mkdir()
    target = pkg / "cli.py"
    target.write_text(SOURCE, encoding="utf-8")
    return target


def test_identical_findings_are_reported_once(tmp_path: Path) -> None:
    """The same rule must not report one defect twice for one file."""
    target = _write(tmp_path)
    cfg = Config(project_root=tmp_path, package_name="myapp")

    issues = Scanner(cfg).scan_sources({target: SOURCE}).get(target, [])

    keys = [(i.rule_id, str(i.file), i.line, i.col, i.message) for i in issues]
    assert len(keys) == len(set(keys)), "scanner emitted duplicate issues"


def test_relative_imports_counted_once_per_import(tmp_path: Path) -> None:
    """Two relative imports yield two findings, not four."""
    target = _write(tmp_path)
    cfg = Config(project_root=tmp_path, package_name="myapp")

    issues = Scanner(cfg).scan_sources({target: SOURCE}).get(target, [])
    relative = [i for i in issues if i.rule_id == "relative-imports"]

    assert len(relative) == 2
    assert {i.line for i in relative} == {3, 4}


def test_composite_honours_a_disabled_sub_rule(tmp_path: Path) -> None:
    """Disabling a rule id also silences it inside a composite."""
    cfg = Config(
        project_root=tmp_path,
        package_name="myapp",
        rules={"relative-imports": RuleConfig(enabled=False)},
    )

    tool_ids = {tool.rule_id for tool in CompositeImportRules(cfg).tools}

    assert "relative-imports" not in tool_ids


def test_disabled_rule_produces_no_issues_at_all(tmp_path: Path) -> None:
    """End to end: a disabled rule contributes nothing to a scan."""
    target = _write(tmp_path)
    cfg = Config(
        project_root=tmp_path,
        package_name="myapp",
        rules={"relative-imports": RuleConfig(enabled=False)},
    )

    issues = Scanner(cfg).scan_sources({target: SOURCE}).get(target, [])

    assert not [i for i in issues if i.rule_id == "relative-imports"]
