#!/usr/bin/env python3
"""Example of using prefact programmatically."""

import argparse
from pathlib import Path

from prefact.config import Config
from prefact.engine import RefactoringEngine
from prefact.models import PipelineResult


def run_engine(config: Config) -> PipelineResult:
    """Create the engine for a config and run it."""
    engine = RefactoringEngine(config)
    return engine.run()


def run_prefact_example(
    project_path: Path, config_file: Path = None, dry_run: bool = False
):
    """Run prefact on a project and display results."""

    # Create configuration
    if config_file and config_file.exists():
        print(f"Loading config from {config_file}")
        config = Config.from_yaml(config_file)
    else:
        print("Using default configuration")
        config = Config()

    # Override project path
    config.project_root = project_path.resolve()

    # Set dry run mode
    config.dry_run = dry_run

    # Create and run engine
    print(f"\n🔍 Scanning {project_path}")
    print(f"Package: {config.package_name or 'auto-detect'}")
    print(f"Dry run: {dry_run}")
    print("-" * 50)

    result = run_engine(config)

    # Display results
    print("\n📊 Results:")
    print(f"  Total issues: {result.total_issues}")
    print(f"  Issues fixed: {result.total_fixed}")
    print(f"  Validation passed: {result.all_valid}")

    # Show issues by rule
    issues_by_rule = {}
    for issue in result.issues_found:
        issues_by_rule.setdefault(issue.rule_id, []).append(issue)

    if issues_by_rule:
        print("\n📋 Issues by rule:")
        for rule_id, issues in issues_by_rule.items():
            print(f"  {rule_id}: {len(issues)} issues")

    # Show fix details
    if result.fixes_applied:
        print("\n🔧 Fixes applied:")
        for fix in result.fixes_applied[:5]:  # Show first 5
            print(f"  {fix.file}:{fix.issue.line} - {fix.issue.message}")
        if len(result.fixes_applied) > 5:
            print(f"  ... and {len(result.fixes_applied) - 5} more")

    # Show validation failures
    failed_validations = [v for v in result.validations if not v.passed]
    if failed_validations:
        print("\n❌ Validation failures:")
        for failure in failed_validations:
            print(f"  {failure.file}: {', '.join(failure.errors)}")

    return result


def custom_rule_example():
    """Example of using prefact with custom rules."""
    print("\n" + "=" * 50)
    print("CUSTOM RULE EXAMPLE")
    print("=" * 50)

    # Create a temporary project with custom rules
    temp_dir = Path("temp_custom_project")
    temp_dir.mkdir(exist_ok=True)

    # Create a file with TODO comments
    test_file = temp_dir / "test.py"
    test_file.write_text("""
# TODO: Implement this function
def incomplete_function():
    pass

# TODO: Add error handling
# TODO: Write tests
def another_function():
    print("debug")
""")

    # Create config with custom rules
    config = Config()
    config.project_root = temp_dir.resolve()
    config.package_name = "temp_project"

    # Import custom rules
    try:
        from examples.custom_rules.no_todo_rule import NoTodoRule

        print("✅ Custom rules loaded")
    except ImportError:
        print("⚠️ Could not load custom rules")
        return

    # Run with custom rules
    result = run_engine(config)

    print("\nCustom rule results:")
    print(
        f"  TODO comments found: {len([i for i in result.issues_found if 'todo' in i.rule_id])}"
    )

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir)


def batch_processing_example():
    """Example of processing multiple projects."""
    print("\n" + "=" * 50)
    print("BATCH PROCESSING EXAMPLE")
    print("=" * 50)

    # List of projects to process
    projects = [
        Path("../sample-project"),
        Path("../01-individual-rules/relative-imports"),
        Path("../02-multiple-rules"),
    ]

    results = []

    for project in projects:
        if project.exists():
            print(f"\nProcessing {project.name}...")
            config = Config()
            config.project_root = project.resolve()
            config.dry_run = True  # Don't actually fix

            result = run_engine(config)

            results.append(
                {
                    "project": project.name,
                    "issues": result.total_issues,
                    "fixable": len([i for i in result.issues_found if i.suggested]),
                }
            )
        else:
            print(f"⚠️ Project {project} not found")

    # Summary table
    print("\n📊 Batch Summary:")
    print(f"{'Project':<30} {'Issues':<10} {'Fixable':<10}")
    print("-" * 50)
    for r in results:
        print(f"{r['project']:<30} {r['issues']:<10} {r['fixable']:<10}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="prefact API Usage Example")
    parser.add_argument(
        "--path", type=Path, default=Path("."), help="Project path to scan"
    )
    parser.add_argument("--config", type=Path, help="Configuration file")
    parser.add_argument("--dry-run", action="store_true", help="Don't apply fixes")
    parser.add_argument(
        "--custom-rules", action="store_true", help="Run custom rule example"
    )
    parser.add_argument(
        "--batch", action="store_true", help="Run batch processing example"
    )

    args = parser.parse_args()

    # Main example
    result = run_prefact_example(args.path, args.config, args.dry_run)

    # Additional examples
    if args.custom_rules:
        custom_rule_example()

    if args.batch:
        batch_processing_example()

    # Return exit code based on results
    return 1 if result.total_issues > 0 else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
