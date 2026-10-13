"""Tests for Scanner directory pruning and fast file collection."""

from pathlib import Path

from prefact.config import Config
from prefact.scanner import Scanner


def test_scanner_prunes_heavy_and_local_directories(tmp_path: Path) -> None:
    """Scanner must prune heavy directories and .local folders topdown."""
    # Create normal source
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text("print('hello')\n", encoding="utf-8")

    # Create directories that should be pruned
    for heavy_dir_name in ["c2004", "c2004-git-backup", "workshop", "managed_components", "vendor", "test.local"]:
        h_dir = tmp_path / heavy_dir_name
        h_dir.mkdir()
        (h_dir / "heavy.py").write_text("print('should be ignored')\n", encoding="utf-8")
        (h_dir / "nested").mkdir()
        (h_dir / "nested" / "deep.py").write_text("print('deep')\n", encoding="utf-8")

    # Non-python files that should not be collected
    (src_dir / "data.xml").write_text("<xml/>\n", encoding="utf-8")

    cfg = Config(project_root=tmp_path, include=["**/*.py"])
    scanner = Scanner(cfg)
    collected = scanner.collect_files()

    collected_rel = [str(f.relative_to(tmp_path)) for f in collected]
    assert collected_rel == ["src/app.py"]
