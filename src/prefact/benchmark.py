#!/usr/bin/env python3
"""Prefact performance benchmark.

Reuses the generic benchmark framework from regix.benchmark and adds
prefact-specific probes: ScanProbe (engine throughput) and in-process
scanner throughput.

Usage:
    python -m prefact.benchmark                   # run all suites
    python -m prefact.benchmark --suite startup   # only startup probes
    python -m prefact.benchmark --suite tests     # only test-time probes
    python -m prefact.benchmark --suite scan      # only scan probes
    python -m prefact.benchmark --json            # JSON output
    python -m prefact.benchmark --threshold 2.0   # fail if any probe > 2.0s
"""

import argparse
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional

from regix.benchmark import (
    BenchmarkProbe,
    BenchmarkReporter,
    BenchmarkResult,
    BenchmarkSuite,
    CLIProbe,
    ImportProbe,
    ThroughputProbe,
    UnitTestProbe,
)

_ROOT = Path(__file__).parent.parent.parent  # src/prefact/ -> project root


# ---------------------------------------------------------------------------
# Prefact-specific probes
# ---------------------------------------------------------------------------


class ScanProbe(BenchmarkProbe):
    """Prefact-specific: creates N temp Python files and measures scan throughput."""

    suite = "scan"

    def __init__(
        self,
        num_files: int = 100,
        file_size_kb: int = 1,
        label: Optional[str] = None,
        threshold: Optional[float] = None,
    ):
        self.num_files = num_files
        self.file_size_kb = file_size_kb
        self.label = label or f"scan {num_files}×{file_size_kb}KB"
        self.threshold = threshold

    def run(self) -> BenchmarkResult:
        try:
            from prefact.config import Config
            from prefact.engine import RefactoringEngine
        except ImportError as e:
            return BenchmarkResult(
                name=self.label,
                suite=self.suite,
                elapsed=0.0,
                error=f"prefact not importable: {e}",
                threshold=self.threshold,
            )

        template = textwrap.dedent("""\
            \"\"\"Module {i}.\"\"\"
            from ....module{mod} import func{fn}
            from os import path
            from os import path
            import sys

            def run():
                return "ok"
        """)

        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            for i in range(self.num_files):
                content = template.format(i=i, mod=i % 10, fn=i % 5)
                if self.file_size_kb > 1:
                    pad = "x" * (self.file_size_kb * 1024 - len(content))
                    content += f"\n# {pad}\n"
                (base / f"m{i:04d}.py").write_text(content, encoding="utf-8")

            config = Config(
                project_root=base,
                package_name="bench",
                dry_run=True,
                verbose=False,
            )
            engine = RefactoringEngine(config)

            t0 = time.perf_counter()
            result = engine.run(dry_run=True)
            elapsed = time.perf_counter() - t0

        files_per_sec = self.num_files / elapsed if elapsed > 0 else 0.0
        return BenchmarkResult(
            name=self.label,
            suite=self.suite,
            elapsed=elapsed,
            threshold=self.threshold,
            extra={
                "files": self.num_files,
                "issues_found": len(result.issues_found),
                "fixes_applied": len(result.fixes_applied),
                "files_per_sec": round(files_per_sec, 1),
            },
        )


# ---------------------------------------------------------------------------
# Default prefact benchmark suite
# ---------------------------------------------------------------------------


def _make_inprocess_probe() -> ThroughputProbe:
    """Benchmark scanner in-process with pre-built files."""
    _state: Dict[str, Any] = {}

    def setup() -> None:
        from prefact.config import Config
        from prefact.scanner import Scanner

        tmpdir = tempfile.mkdtemp()
        base = Path(tmpdir)
        src = textwrap.dedent("""\
            from ..utils import helper
            from os import path
            from os import path
            import sys
            def run(): return 1
        """)
        files = []
        for i in range(20):
            p = base / f"m{i}.py"
            p.write_text(src, encoding="utf-8")
            files.append(p)

        config = Config(
            project_root=base, package_name="bench", dry_run=True, verbose=False
        )
        scanner = Scanner(config)
        _state["scanner"] = scanner
        _state["files"] = files
        _state["base"] = base

    def fn() -> None:
        scanner = _state["scanner"]
        files = _state["files"]
        scanner.scan(files)

    return ThroughputProbe(
        label="scanner.scan (20 files, in-process)",
        fn=fn,
        n=10,
        setup=setup,
        threshold_ops=0.5,  # at least 0.5 full scans per second
    )


def build_prefact_suite() -> BenchmarkSuite:
    suite = BenchmarkSuite("prefact")

    # ── Startup / import ────────────────────────────────────────────────────
    suite.add(ImportProbe("prefact", threshold=2.0))
    suite.add(ImportProbe("prefact.engine", threshold=2.0))
    suite.add(ImportProbe("prefact.rules", threshold=2.0))

    suite.add(
        CLIProbe(
            [sys.executable, "-m", "prefact", "--help"],
            label="prefact --help",
            threshold=3.0,
        )
    )
    suite.add(
        CLIProbe(
            [sys.executable, "-m", "prefact", "scan", "--help"],
            label="prefact scan --help",
            threshold=3.0,
        )
    )

    # ── Unit tests ───────────────────────────────────────────────────────────
    tests_dir = _ROOT / "tests"
    if tests_dir.exists():
        suite.add(
            UnitTestProbe(
                tests_dir,
                label="full test suite",
                threshold=30.0,
            )
        )
        for test_file in sorted(tests_dir.glob("test_*.py")):
            suite.add(
                UnitTestProbe(
                    test_file,
                    label=f"pytest {test_file.name}",
                    threshold=15.0,
                )
            )

    # ── Scan throughput ──────────────────────────────────────────────────────
    suite.add(ScanProbe(num_files=50, file_size_kb=1, threshold=10.0))
    suite.add(ScanProbe(num_files=100, file_size_kb=1, threshold=20.0))
    suite.add(ScanProbe(num_files=200, file_size_kb=5, threshold=40.0))

    # ── In-process throughput ────────────────────────────────────────────────
    suite.add(_make_inprocess_probe())

    return suite


# ---------------------------------------------------------------------------
# Generic helper: benchmark any library
# ---------------------------------------------------------------------------


def benchmark_library(
    module: str,
    cli_commands: Optional[List[List[str]]] = None,
    test_path: Optional[Path] = None,
    threshold_import: float = 3.0,
    threshold_cli: float = 5.0,
    threshold_tests: float = 60.0,
) -> BenchmarkSuite:
    """Generic helper to benchmark *any* installed Python library.

    Example:
        results = benchmark_library(
            module="requests",
            cli_commands=[["python", "-c", "import requests; print(requests.__version__)"]],
        ).run()
    """
    suite = BenchmarkSuite(f"library:{module}")
    suite.add(ImportProbe(module, threshold=threshold_import))

    for cmd in cli_commands or []:
        suite.add(CLIProbe(cmd, threshold=threshold_cli))

    if test_path and test_path.exists():
        suite.add(UnitTestProbe(test_path, threshold=threshold_tests))

    return suite


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Performance benchmark for prefact",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python -m prefact.benchmark                    # all suites
              python -m prefact.benchmark --suite startup    # import + CLI probes only
              python -m prefact.benchmark --suite tests      # unit test probes only
              python -m prefact.benchmark --suite scan       # scan throughput probes
              python -m prefact.benchmark --suite throughput # in-process throughput
              python -m prefact.benchmark --json             # JSON output
        """),
    )
    parser.add_argument(
        "--suite",
        choices=["startup", "tests", "scan", "throughput"],
        default=None,
        help="Run only probes from this suite (default: all)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--plain", action="store_true", help="Plain text (no colours)")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        metavar="SEC",
        help="Override all time thresholds",
    )
    args = parser.parse_args()

    suite = build_prefact_suite()
    results = suite.run(suite_filter=args.suite)

    if args.threshold is not None:
        for r in results:
            if r.unit == "s":
                r.threshold = args.threshold

    fmt = "json" if args.json else ("plain" if args.plain else "auto")
    reporter = BenchmarkReporter(results)
    reporter.print(fmt=fmt)

    return 1 if reporter.any_failed() else 0


if __name__ == "__main__":
    sys.exit(main())
