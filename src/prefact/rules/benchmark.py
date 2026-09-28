"""Performance benchmarks comparing AST vs Ruff implementations.

Run this module to see performance comparisons for your project.
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict

from prefact.config import Config
from prefact.rules import get_all_rules
from prefact.rules.migration import RuleMigrationManager


def benchmark_file(file_path: Path, config: Config) -> Dict:
    """Benchmark a single file with both AST and Ruff implementations."""
    file_content = file_path.read_text(encoding="utf-8")
    migration_manager = RuleMigrationManager(config)

    results = {
        "file": str(file_path),
        "file_size_bytes": len(file_content),
        "lines": file_content.count("\n") + 1,
        "rules": {},
    }

    total_ast_time = 0
    total_ruff_time = 0

    for rule_id in migration_manager.MIGRATION_MAP:
        # Get implementations
        ast_rule_class = get_all_rules().get(rule_id)
        ruff_rule_class = migration_manager.get_migrated_rule(rule_id)

        if not ast_rule_class or not ruff_rule_class:
            continue

        # Profile AST implementation
        ast_rule = ast_rule_class(config)
        ast_start = time.perf_counter()
        ast_issues = ast_rule.scan_file(file_path, file_content)
        ast_time = time.perf_counter() - ast_start

        # Profile Ruff implementation
        ruff_rule = ruff_rule_class(config)
        ruff_start = time.perf_counter()
        ruff_issues = ruff_rule.scan_file(file_path, file_content)
        ruff_time = time.perf_counter() - ruff_start

        # Store results
        results["rules"][rule_id] = {
            "ast": {"issues": len(ast_issues), "time_ms": ast_time * 1000},
            "ruff": {"issues": len(ruff_issues), "time_ms": ruff_time * 1000},
            "speedup": ast_time / ruff_time if ruff_time > 0 else 0,
            "issues_match": len(ast_issues) == len(ruff_issues),
        }

        total_ast_time += ast_time
        total_ruff_time += ruff_time

    results["total"] = {
        "ast_time_ms": total_ast_time * 1000,
        "ruff_time_ms": total_ruff_time * 1000,
        "overall_speedup": total_ast_time / total_ruff_time
        if total_ruff_time > 0
        else 0,
    }

    return results


def benchmark_project(project_root: Path, config: Config) -> Dict:
    """Benchmark entire project."""
    python_files = list(project_root.rglob("*.py"))
    # Filter out test files and __pycache__
    python_files = [
        f for f in python_files if "test" not in f.name and "__pycache__" not in str(f)
    ]

    print(f"Benchmarking {len(python_files)} Python files...")

    all_results = []
    total_ast_time = 0
    total_ruff_time = 0

    for file_path in python_files:
        try:
            file_benchmark = benchmark_file(file_path, config)
            all_results.append(file_benchmark)
            total_ast_time += file_benchmark["total"]["ast_time_ms"]
            total_ruff_time += file_benchmark["total"]["ruff_time_ms"]
        except Exception as e:
            print(f"Error benchmarking {file_path}: {e}")

    return {
        "project_root": str(project_root),
        "files_processed": len(all_results),
        "total_ast_time_ms": total_ast_time,
        "total_ruff_time_ms": total_ruff_time,
        "overall_speedup": total_ast_time / total_ruff_time
        if total_ruff_time > 0
        else 0,
        "results": all_results,
    }


def print_benchmark_results(results: Dict) -> None:
    """Print formatted benchmark results."""
    print("=" * 60)
    print("PERFORMANCE BENCHMARK RESULTS")
    print("=" * 60)

    # Overall summary
    print(f"\nProject: {results['project_root']}")
    print(f"Files processed: {results['files_processed']}")
    print(f"\nTotal AST time: {results['total_ast_time_ms']:.2f} ms")
    print(f"Total Ruff time: {results['total_ruff_time_ms']:.2f} ms")
    print(f"Overall speedup: {results['overall_speedup']:.2f}x")

    # Per-file details
    print("-" * 60)
    print("PER-FILE RESULTS")
    print("-" * 60)

    for file_stats in results["results"]:
        file_name = Path(file_stats["file"]).name
        print(
            f"\n{file_name} ({file_stats['lines']} lines, {file_stats['file_size_bytes']} bytes)"
        )
        print(f"  Speedup: {file_stats['total']['overall_speedup']:.2f}x")

        for rule_id, rule_result in file_stats["rules"].items():
            speedup = rule_result["speedup"]
            match = "✓" if rule_result["issues_match"] else "✗"
            print(f"  {rule_id}: {speedup:.2f}x speedup, issues match: {match}")


def main() -> None:
    """Run benchmark on current project."""
    parser = argparse.ArgumentParser(
        description="Benchmark AST vs Ruff implementations"
    )
    parser.add_argument("--path", default=".", help="Path to benchmark")
    args = parser.parse_args()

    # Load config and run benchmark
    bench_path = Path(args.path)
    benchmark_report = benchmark_project(bench_path, Config(project_root=bench_path))

    # Print results
    print_benchmark_results(benchmark_report)

    # Save detailed results
    output_file = Path("benchmark_results.json")
    with open(output_file, "w") as f:
        json.dump(benchmark_report, f, indent=2)
    print(f"\nDetailed results saved to: {output_file}")
