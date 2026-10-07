"""Command-line interface for prefact."""

from pathlib import Path

import click

from prefact._base import console
from prefact.autonomous import AutonomousRefact
from prefact.config import Config
from prefact.config_extended import ExtendedConfig
from prefact.defaults import DEFAULT_EXCLUDE, DEFAULT_INCLUDE
from prefact.engine import RefactoringEngine
from prefact.reporters import console as console_reporter
from prefact.reporters import json_reporter


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "-a",
    "--autonomous",
    is_flag=True,
    help="Run autonomous mode (initialize, scan, and create tickets).",
)
@click.option(
    "--init-only",
    is_flag=True,
    help="Only initialize prefact.yaml without running full process.",
)
@click.option("--skip-tests", is_flag=True, help="Skip running tests.")
@click.option("--skip-examples", is_flag=True, help="Skip running examples.")
@click.option(
    "-e",
    "--exclude",
    multiple=True,
    help="Exclude patterns (glob syntax). Can be used multiple times.",
)
@click.option(
    "--with-testql/--no-testql",
    "with_testql",
    default=False,
    help="Include TestQL scenarios run as final autonomous step.",
)
@click.option(
    "--testql-dir",
    default=None,
    help="Directory containing *.testql.toon.yaml scenarios (default: testql-scenarios/).",
)
@click.version_option(package_name="prefact")
def main(
    ctx,
    autonomous,
    init_only,
    skip_tests,
    skip_examples,
    exclude,
    with_testql,
    testql_dir,
) -> None:
    """prefact – automatic Python prefactoring toolkit.

    Detect, fix, and validate common code issues - especially those
    introduced by LLMs (e.g. relative imports, unused imports).

    Use 'prefact -a' for autonomous mode.
    """
    try:
        from prefact.autoupdate import check_for_updates

        check_for_updates("prefact")
    except Exception:
        pass

    if autonomous:
        # Auto-skip examples if exclude pattern matches examples directory
        auto_skip_examples = skip_examples
        if exclude and any(
            "examples" in pattern or pattern.startswith("examples")
            for pattern in exclude
        ):
            auto_skip_examples = True
        # Run autonomous command directly with all options
        ctx.invoke(
            autonomous_cmd,
            project_path=".",
            init_only=init_only,
            skip_tests=skip_tests,
            skip_examples=auto_skip_examples,
            exclude=exclude,
            with_testql=with_testql,
            testql_dir=testql_dir,
        )


# ── shared options ────────────────────────────────────────────────────


def _common_options(fn):
    fn = click.option(
        "-p", "--path", "project_path", default=".", help="Project root directory."
    )(fn)
    fn = click.option(
        "--package",
        "package_name",
        default="",
        help="Package name (auto-detected if omitted).",
    )(fn)
    fn = click.option(
        "-c",
        "--config",
        "config_file",
        default=None,
        help="Path to prefact.yaml config.",
    )(fn)
    fn = click.option(
        "-e",
        "--exclude",
        multiple=True,
        help="Exclude patterns (glob syntax). Can be used multiple times.",
    )(fn)
    fn = click.option("--verbose", is_flag=True, help="Show detailed output.")(fn)
    fn = click.option(
        "--format",
        "output_format",
        type=click.Choice(["console", "json"]),
        default="console",
    )(fn)
    fn = click.option(
        "-o", "--output", "output_file", default=None, help="Write JSON report to file."
    )(fn)
    fn = click.option(
        "--allow-dirty-checkout",
        is_flag=True,
        help="Bypass Wellmanifest guard and allow in-place modification on main/primary checkout.",
    )(fn)
    return fn


def _build_config(
    project_path, package_name, config_file, verbose, exclude=None, **_kw
) -> Config:
    if config_file:
        # Try extended config first, fall back to basic config
        try:
            cfg = ExtendedConfig.from_yaml(Path(config_file))
        except Exception:
            cfg = Config.from_yaml(Path(config_file))
    else:
        # Auto-discover prefact.yaml
        candidate = Path(project_path).resolve() / "prefact.yaml"
        if candidate.exists():
            # Try extended config first, fall back to basic config
            try:
                cfg = ExtendedConfig.from_yaml(candidate)
            except Exception:
                cfg = Config.from_yaml(candidate)
        else:
            cfg = Config()
    cfg.project_root = Path(project_path).resolve()
    if package_name:
        cfg.package_name = package_name
    cfg.verbose = verbose
    if "allow_dirty_checkout" in _kw:
        cfg.allow_dirty_checkout = bool(_kw["allow_dirty_checkout"])
    # Merge CLI exclude patterns with config file patterns
    if exclude:
        cfg.exclude = list(cfg.exclude) + list(exclude)
    return cfg


# ── commands ──────────────────────────────────────────────────────────


@main.command()
@_common_options
def scan(**kwargs) -> None:
    """Scan for issues without applying fixes."""
    cfg = _build_config(**kwargs)
    scan_report = RefactoringEngine(cfg).scan_only()
    _output(scan_report, kwargs)


@main.command()
@_common_options
@click.option(
    "--dry-run", is_flag=True, help="Show what would change without writing files."
)
@click.option("--no-backup", is_flag=True, help="Don't create .bak backup files.")
@click.option(
    "--worktree",
    is_flag=True,
    help="Execute refactoring inside an isolated Wellmanifest ticket worktree allocated via ./project/new-ticket.sh.",
)
@click.option(
    "--auto-merge/--no-auto-merge",
    default=True,
    help="When using --worktree, automatically merge into main if governance check passes.",
)
def fix(dry_run, no_backup, worktree, auto_merge, **kwargs) -> None:
    """Scan, fix, and validate in one pass."""
    cfg = _build_config(**kwargs)
    cfg.dry_run = dry_run
    cfg.backup = not no_backup

    if worktree and not dry_run:
        from prefact.wellmanifest import WellmanifestWorktreeManager, find_wellmanifest_root

        repo_root = find_wellmanifest_root(cfg.project_root)
        if not repo_root:
            console.print(
                "[bold yellow]⚠️ No Wellmanifest repository found with project/new-ticket.sh. Running standard fix...[/bold yellow]"
            )
        else:
            mgr = WellmanifestWorktreeManager(repo_root)
            if not mgr.can_allocate():
                console.print(
                    f"[bold red]❌ Cannot allocate ticket: {mgr.new_ticket_script} is missing or not executable.[/bold red]"
                )
                raise SystemExit(1)

            scan_report = RefactoringEngine(cfg).scan_only()
            if not scan_report.issues_found:
                console.print("[bold green]✅ No issues found to fix.[/bold green]")
                return

            files_to_fix = sorted(
                list(
                    set(
                        str(issue.file.resolve().relative_to(repo_root.resolve()))
                        for issue in scan_report.issues_found
                        if issue.file.resolve().is_relative_to(repo_root.resolve())
                    )
                )
            )
            if not files_to_fix:
                console.print("[bold yellow]No files to fix inside this repository.[/bold yellow]")
                return

            title = f"Prefact: fix {len(scan_report.issues_found)} issues across {len(files_to_fix)} files"
            allocation = mgr.allocate_ticket(title=title, owned_paths=files_to_fix)

            wt_cfg = _build_config(**kwargs)
            wt_cfg.project_root = allocation.worktree_path
            wt_cfg.backup = not no_backup
            wt_cfg.allow_dirty_checkout = True  # Safe inside ticket worktree

            wt_report = RefactoringEngine(wt_cfg).run()
            _output(wt_report, kwargs)

            if auto_merge:
                decision = mgr.evaluate_merge_disposition(allocation)
                console.print(f"[bold cyan]Merge disposition:[/bold cyan] {decision['disposition']}")
                if decision["disposition"] == "adopt":
                    mgr.merge_ticket(allocation)
                else:
                    console.print(
                        f"[bold yellow]Ticket {allocation.ticket_id} left in worktree {allocation.worktree_path} (disposition: {decision['disposition']}).[/bold yellow]"
                    )
            return

    fix_report = RefactoringEngine(cfg).run()
    _output(fix_report, kwargs)
    if not fix_report.all_valid:
        raise SystemExit(1)


@main.command()
@_common_options
@click.argument("filepath")
def check(filepath, **kwargs) -> None:
    """Scan a single file."""
    cfg = _build_config(**kwargs)
    file_report = RefactoringEngine(cfg).run_file(Path(filepath), dry_run=True)
    _output(file_report, kwargs)


@main.command()
@click.option(
    "-p", "--path", "project_path", default=".", help="Where to create prefact.yaml."
)
def init(project_path) -> None:
    """Generate a default prefact.yaml in the project directory."""
    exclude_lines = "".join(f'  - "{p}"\n' for p in DEFAULT_EXCLUDE)
    include_lines = "".join(f'  - "{p}"\n' for p in DEFAULT_INCLUDE)
    default = f"""\
# prefact.yaml – configuration for prefact
# package_name: mypackage     # auto-detected from pyproject.toml if omitted

include:
{include_lines}
exclude:
{exclude_lines}
# Keys must be rule ids, exactly as a rule reports them — `prefact check`
# prints the id in its Rule column. A key that matches no rule configures
# nothing silently, because an unlisted rule defaults to enabled.
#
# prefact ships one rule per (defect, tool) pair, so a defect has several ids.
# Enabling one does not disable its siblings; list the ones you do not want.
rules:
  relative-imports:
    enabled: true
    severity: warning
  no-relative-imports:
    enabled: false

  ruff-unused-imports:
    enabled: true
    severity: info
  ast-unused-imports:
    enabled: false
  autoflake-unused-imports:
    enabled: false
  importchecker-unused-imports:
    enabled: false
  unimport-unused-imports:
    enabled: false

  ruff-duplicate-imports:
    enabled: true
    severity: warning
  ast-duplicate-imports:
    enabled: false
  importchecker-duplicate-imports:
    enabled: false
  unimport-duplicate-imports:
    enabled: false

  ruff-wildcard-imports:
    enabled: true
    severity: error
  ast-wildcard-imports:
    enabled: false
  unimport-star-imports:
    enabled: false

  ruff-sorted-imports:
    enabled: false
    severity: info
  ast-sorted-imports:
    enabled: false

  ast-string-concat:
    enabled: true
    severity: info
  pylint-string-concat:
    enabled: false

  ruff-print-statements:
    enabled: true
    severity: info
    options:
      ignore_patterns: ["cli.py", "scripts/"]
  ast-print-statements:
    enabled: false
  pylint-print-statements:
    enabled: false

  mypy-missing-return-type:
    enabled: false
    severity: info
  ast-missing-return-type:
    enabled: false
  smart-return-type:
    enabled: false

  # Composites re-run the rules above; leave them off unless you want their
  # parallel strategy instead of the standalone rules.
  composite-imports:
    enabled: false
  composite-unused-imports:
    enabled: false
  composite-type-checking:
    enabled: false
"""
    dest = Path(project_path).resolve() / "prefact.yaml"
    if dest.exists():
        click.echo(f"File already exists: {dest}")
        raise SystemExit(1)
    dest.write_text(default)
    click.echo(f"Created {dest}")


@main.command()
@click.option(
    "-p", "--path", "project_path", default=".", help="Project root directory."
)
@click.option(
    "--init-only",
    is_flag=True,
    help="Only initialize prefact.yaml without running full process.",
)
@click.option("--skip-tests", is_flag=True, help="Skip running tests.")
@click.option("--skip-examples", is_flag=True, help="Skip running examples.")
@click.option(
    "-e",
    "--exclude",
    multiple=True,
    help="Exclude patterns (glob syntax). Can be used multiple times.",
)
@click.option(
    "--with-testql/--no-testql",
    "with_testql",
    default=False,
    help="Include TestQL scenarios run as final autonomous step.",
)
@click.option(
    "--testql-dir",
    default=None,
    help="Directory containing *.testql.toon.yaml scenarios (default: testql-scenarios/).",
)
def autonomous_cmd(
    project_path, init_only, skip_tests, skip_examples, exclude, with_testql, testql_dir
) -> None:
    """Run autonomous prefact mode (-a).

    Automatically initializes prefact.yaml if missing, runs examples,
    scans for issues, and creates tickets in planfile.yaml.
    """
    # Initialize autonomous prefact
    auto = AutonomousRefact(
        Path(project_path), exclude_patterns=list(exclude) if exclude else None
    )

    if init_only:
        if not auto.refact_config_path.exists():
            console.print("📝 Creating prefact.yaml configuration...")
            auto.create_prefact_config()
            console.print("✅ Initialization complete!", style="green")
        else:
            console.print("ℹ️ prefact.yaml already exists", style="blue")
        return

    # Run full autonomous process
    autonomous_ok = auto.run_autonomous(
        skip_examples=skip_examples,
        with_testql=with_testql,
        testql_scenarios_dir=testql_dir,
    )

    if not autonomous_ok:
        raise SystemExit(1)


@main.command("testql")
@click.argument("scenario_path")
@click.option(
    "-p", "--path", "project_path", default=".", help="Project root directory."
)
@click.option("--url", default="http://localhost:8101", help="Base API URL for TestQL.")
@click.option(
    "--dry-run", is_flag=True, help="Parse/validate scenario without full execution."
)
@click.option(
    "-s",
    "--strategy",
    "strategy_path",
    default=None,
    help="Target planfile YAML (default: <project>/planfile.yaml).",
)
@click.option(
    "--create-tickets/--no-create-tickets",
    default=True,
    help="Create planfile tickets for TestQL failures.",
)
@click.option(
    "--sync/--no-sync",
    "sync_targets",
    default=True,
    help="Sync generated tickets to TODO.md and configured integrations.",
)
@click.option(
    "--max-tickets",
    default=25,
    type=int,
    show_default=True,
    help="Maximum tickets generated from one TestQL run.",
)
@click.option("--testql-bin", default="testql", help="TestQL CLI executable name/path.")
@click.option(
    "--testql-repo-path",
    default="/home/tom/github/oqlos/testql",
    help="Fallback path to local TestQL repository.",
)
def testql_cmd(
    scenario_path,
    project_path,
    url,
    dry_run,
    strategy_path,
    create_tickets,
    sync_targets,
    max_tickets,
    testql_bin,
    testql_repo_path,
) -> None:
    """Run TestQL DSL validation and bridge results into planfile/TODO."""
    auto = AutonomousRefact(Path(project_path))
    payload = auto.run_testql(
        scenario_path=scenario_path,
        url=url,
        dry_run=dry_run,
        create_tickets=create_tickets,
        sync_targets=sync_targets,
        max_tickets=max_tickets,
        testql_bin=testql_bin,
        testql_repo_path=testql_repo_path,
        strategy_path=strategy_path,
    )

    if not payload.get("validation", {}).get("ok", True):
        raise SystemExit(1)


@main.command()
def rules() -> None:
    """List all available rules."""
    from rich.table import Table

    from prefact.rules import get_all_rules

    table = Table(title="Available Rules")
    table.add_column("Rule ID", style="bold")
    table.add_column("Description")
    table.add_column("Auto-fix")
    for rule_id, rule_cls in sorted(get_all_rules().items()):
        # Heuristic: if fix() returns source unchanged, it's scan-only
        has_fix = rule_id in (
            "relative-imports",
            "ast-unused-imports",
            "ast-duplicate-imports",
        )
        table.add_row(
            rule_id, rule_cls.description, "✅" if has_fix else "🔍 scan-only"
        )
    console.print(table)


# ── helpers ───────────────────────────────────────────────────────────


def _output(report, kwargs) -> None:
    fmt = kwargs.get("output_format", "console")
    if fmt == "json":
        text = json_reporter.dump(
            report,
            output=Path(kwargs["output_file"]) if kwargs.get("output_file") else None,
        )
        if not kwargs.get("output_file"):
            click.echo(text)
    else:
        console_reporter.print_report(report, verbose=kwargs.get("verbose", False))


if __name__ == "__main__":
    main()
