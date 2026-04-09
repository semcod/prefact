<!-- code2docs:start --># prefact

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.8-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-738-green)
> **738** functions | **143** classes | **102** files | CC̄ = 3.0

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/semcod/refactoring](https://github.com/semcod/refactoring)

## Installation

### From PyPI

```bash
pip install prefact
```

### From Source

```bash
git clone https://github.com/semcod/refactoring
cd prefact
pip install -e .
```

### Optional Extras

```bash
pip install prefact[ruff]    # ruff features
pip install prefact[mypy]    # mypy features
pip install prefact[isort]    # isort features
pip install prefact[autoflake]    # autoflake features
pip install prefact[pylint]    # pylint features
pip install prefact[unimport]    # unimport features
pip install prefact[importchecker]    # importchecker features
pip install prefact[import-linter]    # import-linter features
pip install prefact[performance]    # performance features
pip install prefact[monitoring]    # monitoring features
pip install prefact[dev]    # development tools
pip install prefact[docs]    # documentation tools
pip install prefact[all]    # all optional features
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
prefact ./my-project

# Only regenerate README
prefact ./my-project --readme-only

# Preview what would be generated (no file writes)
prefact ./my-project --dry-run

# Check documentation health
prefact check ./my-project

# Sync — regenerate only changed modules
prefact sync ./my-project
```

### Python API

```python
from prefact import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```

## Generated Output

When you run `prefact`, the following files are produced:

```
<project>/
├── README.md                 # Main project README (auto-generated sections)
├── docs/
│   ├── api.md               # Consolidated API reference
│   ├── modules.md           # Module documentation with metrics
│   ├── architecture.md      # Architecture overview with diagrams
│   ├── dependency-graph.md  # Module dependency graphs
│   ├── coverage.md          # Docstring coverage report
│   ├── getting-started.md   # Getting started guide
│   ├── configuration.md    # Configuration reference
│   └── api-changelog.md    # API change tracking
├── examples/
│   ├── quickstart.py       # Basic usage examples
│   └── advanced_usage.py   # Advanced usage examples
├── CONTRIBUTING.md         # Contribution guidelines
└── mkdocs.yml             # MkDocs site configuration
```

## Configuration

Create `prefact.yaml` in your project root (or run `prefact init`):

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

readme:
  sections:
    - overview
    - install
    - quickstart
    - api
    - structure
  badges:
    - version
    - python
    - coverage
  sync_markers: true

docs:
  api_reference: true
  module_docs: true
  architecture: true
  changelog: true

examples:
  auto_generate: true
  from_entry_points: true

sync:
  strategy: markers    # markers | full | git-diff
  watch: false
  ignore:
    - "tests/"
    - "__pycache__"
```

## Sync Markers

prefact can update only specific sections of an existing README using HTML comment markers:

```markdown
<!-- prefact:start -->
# Project Title
... auto-generated content ...
<!-- prefact:end -->
```

Content outside the markers is preserved when regenerating. Enable this with `sync_markers: true` in your configuration.

## Architecture

```
prefact/
├── project    ├── run_all    ├── generate_examples            ├── before            ├── after├── benchmark_ram_optimization            ├── after    ├── run_examples            ├── before            ├── after            ├── before            ├── after            ├── before            ├── after            ├── before            ├── after            ├── before            ├── after            ├── before        ├── messy_module        ├── cli        ├── utils        ├── core        ├── sample_code        ├── models        ├── custom_rules/            ├── no_todo_rule        ├── example        ├── engine        ├── validator        ├── git_hooks        ├── config        ├── autonomous/        ├── fixer    ├── prefact/            ├── after        ├── scanner            ├── before        ├── _base            ├── exceptions        ├── logging/        ├── models            ├── levels            ├── logger        ├── cli            ├── builtin            ├── cache_state        ├── plugins/        ├── performance/            ├── parallel            ├── cache_adapters        ├── reporters/            ├── console            ├── cache            ├── json_reporter            ├── docs_manager            ├── todo_manager            ├── setup_manager            ├── project_scanner            ├── dependency_checker            ├── _base            ├── config            ├── generator        ├── config_extended/            ├── validation            ├── utils            ├── validators            ├── models            ├── constants            ├── magic_numbers            ├── ruff_based            ├── unused_imports            ├── importchecker_based            ├── composite_factory            ├── pylint_based            ├── registry            ├── strategies            ├── type_hints        ├── rules/            ├── wildcard_imports            ├── string_concat            ├── ai_boilerplate            ├── _ast_cache            ├── import_linter_based            ├── formatters            ├── unimport_based            ├── llm_generated_code            ├── sorted_imports        ├── benchmark            ├── isort_based            ├── benchmark            ├── migration            ├── llm_hallucinations            ├── autoflake_based            ├── composite_rules            ├── duplicate_imports            ├── print_statements        ├── extension            ├── relative_imports            ├── string_transformations            ├── mypy_based```

## API Overview

### Classes

- **`Processor`** — Processor class with relative imports.
- **`Processor`** — Processor class with absolute imports.
- **`Processor`** — Processor class.
- **`Processor`** — Processor class.
- **`DataProcessor`** — A class with clean imports.
- **`DataProcessor`** — A class with unused imports.
- **`DataProcessor`** — A class with various issues.
- **`UtilClass`** — Utility class.
- **`DataProcessor`** — A class that processes data.
- **`User`** — User model.
- **`Post`** — Post model.
- **`NoTodoRule`** — Rule that detects TODO comments in code.
- **`NoPrintRule`** — Custom rule that detects print statements (alternative to built-in).
- **`RefactoringEngine`** — Main entry point: scan the project, apply fixes, validate results.
- **`Validator`** — —
- **`GitHooks`** — Manages Git hooks for prefact.
- **`PreCommitConfig`** — Generate pre-commit configuration for prefact.
- **`RuleConfig`** — Configuration for a single rule.
- **`Config`** — Top-level configuration.
- **`Fixer`** — —
- **`Scanner`** — Discovers Python files and runs all enabled rules against them.
- **`PprefactException`** — —
- **`ConfigurationError`** — —
- **`RuleError`** — —
- **`PluginError`** — —
- **`Severity`** — How critical an issue is.
- **`Phase`** — Pipeline phase.
- **`Issue`** — A single detected problem in the codebase.
- **`Fix`** — A concrete code change to apply.
- **`ValidationResult`** — Result of post-fix validation.
- **`PipelineResult`** — Aggregate result of the full scan → fix → validate pipeline.
- **`LogLevel`** — Log levels for prefact.
- **`LogLevel`** — —
- **`PprefactLogger`** — —
- **`PluginMetadata`** — Metadata for a loaded plugin.
- **`PluginValidator`** — Validates plugins before loading.
- **`PluginManager`** — Manages loading and registration of plugins.
- **`ParallelScanTask`** — A task for parallel scanning.
- **`ParallelEngine`** — Parallel processing engine for prefact.
- **`ParallelScanner`** — High-level interface for parallel scanning.
- **`PerformanceMonitor`** — Monitor performance of parallel operations.
- **`ScanResultCache`** — Specialized cache for scan results.
- **`ConfigCache`** — Cache for rule configurations.
- **`RuleResultCache`** — Cache for individual rule results.
- **`FileHashCache`** — Cache for file hashes.
- **`Cache`** — Wrapper for diskcache with additional functionality.
- **`ScanResultCache`** — Specialized cache for scan results.
- **`ConfigCache`** — Cache for rule configurations.
- **`RuleResultCache`** — Cache for individual rule results.
- **`FileHashCache`** — Cache for file hashes.
- **`CacheContext`** — Context manager for cache operations.
- **`DocsManager`** — Manages documentation files - planfile.yaml and CHANGELOG.md.
- **`TodoManager`** — Manages TODO.md file operations.
- **`SetupManager`** — Handles project setup - configuration and examples.
- **`ProjectScanner`** — Handles project scanning operations.
- **`DependencyChecker`** — Checks for outdated project dependencies.
- **`BaseManager`** — Base class for autonomous managers.
- **`ExtendedConfig`** — Extended configuration with additional features.
- **`ConfigGenerator`** — Generate configuration files.
- **`ConfigValidator`** — Validate configuration files.
- **`ConfigValidator`** — —
- **`ExtendedConfig`** — —
- **`MagicNumberRule`** — Detect magic numbers in code.
- **`RuffHelper`** — Helper class for Ruff operations.
- **`RuffWildcardImports`** — Wildcard imports detection using Ruff.
- **`RuffPrintStatements`** — Print statements detection using Ruff.
- **`RuffUnusedImports`** — Unused imports detection and removal using Ruff.
- **`RuffSortedImports`** — Import sorting using Ruff.
- **`RuffDuplicateImports`** — Duplicate imports detection using Ruff.
- **`UnusedImports`** — —
- **`ImportCheckerHelper`** — Helper class for importchecker operations.
- **`ImportCheckerUnusedImports`** — Detect unused imports using importchecker.
- **`ImportCheckerDuplicateImports`** — Detect duplicate imports using importchecker.
- **`ImportDependencyAnalysis`** — Analyze import dependencies using importchecker.
- **`ImportOptimizer`** — Optimize imports based on importchecker analysis.
- **`CompositeRuleFactory`** — Factory for creating composite rules dynamically.
- **`PylintHelper`** — Helper class for Pylint operations.
- **`PylintPrintStatements`** — Detect print statements using Pylint.
- **`PylintStringConcat`** — Detect string concatenation using Pylint.
- **`PprefactPylintPlugin`** — Custom Pylint plugin for prefact-specific checks.
- **`PylintComprehensive`** — Comprehensive analysis using Pylint with custom rules.
- **`LazyRuleRegistry`** — Registry that lazily loads rule classes.
- **`ToolStrategy`** — Abstract base class for tool orchestration strategies.
- **`ParallelScanStrategy`** — Run all tools in parallel and merge results.
- **`SequentialScanStrategy`** — Run tools sequentially, passing results between them.
- **`PriorityBasedStrategy`** — Use tool priority to resolve conflicts.
- **`MissingReturnType`** — —
- **`AutonomousRefact`** — Autonomous prefact manager.
- **`BaseRule`** — Base class every prefactoring rule must implement.
- **`WildcardImports`** — —
- **`StringConcatToFstring`** — —
- **`AIBoilerplateRule`** — Detect AI boilerplate and template code.
- **`ImportLinterHelper`** — Helper class for import-linter operations.
- **`ImportLinterLayers`** — Enforce import layering rules using import-linter.
- **`ImportLinterNoRelative`** — Block relative imports using import-linter.
- **`ImportLinterIndependence`** — Ensure module independence using import-linter.
- **`ImportLinterCustomArchitecture`** — Enforce custom architectural rules using import-linter.
- **`JsonFormatter`** — —
- **`UnimportHelper`** — Helper class for unimport operations.
- **`UnimportUnusedImports`** — Remove unused imports using unimport.
- **`UnimportDuplicateImports`** — Remove duplicate imports using unimport.
- **`UnimportStarImports`** — Handle star imports using unimport.
- **`UnimportAll`** — Apply all unimport fixes.
- **`LLMGeneratedCodeRule`** — Detect code that appears to be LLM-generated.
- **`SortedImports`** — —
- **`ScanProbe`** — Prefact-specific: creates N temp Python files and measures scan throughput.
- **`ISortHelper`** — Helper class for ISort operations.
- **`ISortedImports`** — Sort imports using ISort.
- **`ImportSectionSeparator`** — Ensure import sections are properly separated.
- **`CustomImportOrganization`** — Organize imports according to custom rules.
- **`RuleMigrationManager`** — Manages migration from AST-based rules to Ruff-based rules.
- **`HybridScanner`** — Scanner that can use both AST and Ruff-based rules.
- **`PerformanceProfiler`** — Compare performance between AST and Ruff implementations.
- **`LLMHallucinationRule`** — Detect LLM hallucination patterns in code.
- **`AutoflakeHelper`** — Helper class for Autoflake operations.
- **`AutoflakeUnusedImports`** — Remove unused imports using Autoflake.
- **`AutoflakeUnusedVariables`** — Remove unused variables using Autoflake.
- **`AutoflakeDuplicateKeys`** — Remove duplicate keys in dictionaries using Autoflake.
- **`AutoflakeAll`** — Apply all Autoflake fixes: unused imports, variables, and duplicate keys.
- **`CompositeUnusedImports`** — Composite rule for unused imports using multiple tools.
- **`CompositeImportRules`** — Composite rule for all import-related checks.
- **`CompositeTypeChecking`** — Composite rule for type checking using multiple tools.
- **`DuplicateImports`** — —
- **`PrintStatements`** — —
- **`PrefactIssue`** — —
- **`PrefactResult`** — —
- **`PrefactDiagnosticsProvider`** — —
- **`PrefactTreeItem`** — —
- **`PrefactTreeProvider`** — —
- **`RelativeToAbsoluteImports`** — —
- **`StringConcatTransformer`** — Transform string concatenations to f-strings.
- **`StringConcatToFString`** — Convert string concatenations to f-strings.
- **`FlyntHelper`** — Helper for using flynt library for string formatting.
- **`FlyntStringFormatting`** — Use flynt library for string formatting optimizations.
- **`ContextAwareStringTransformer`** — Transform string concatenations with context awareness.
- **`ContextAwareStringConcat`** — Context-aware string concatenation to f-string conversion.
- **`MyPyHelper`** — Helper class for MyPy operations.
- **`MyPyMissingReturnType`** — Detect missing return type annotations using MyPy.
- **`MyPyTypeChecking`** — General type checking using MyPy.
- **`ReturnTypeInferrer`** — Infer return types for simple functions.
- **`ReturnTypeAdder`** — Transformer to add return type annotations to functions.
- **`SmartReturnTypeRule`** — Smart return type detection with inference suggestions.

### Functions

- `print_status()` — —
- `print_warning()` — —
- `print_error()` — —
- `process_user(user_id)` — Process a user.
- `process_user(user_id)` — Process a user.
- `create_test_files(base_dir, num_files, file_size_kb)` — Create test Python files with import issues to benchmark against.
- `benchmark_without_rampreload(config)` — Run benchmark without RAM preloading (original implementation).
- `benchmark_with_rampreload(config)` — Run benchmark with RAM preloading (optimized implementation).
- `run_benchmark(num_files, file_size_kb)` — Run a complete benchmark comparing both implementations.
- `main()` — Run multiple benchmarks with different file counts and sizes.
- `add(a, b)` — Add two numbers.
- `get_user(user_id)` — Get user by ID.
- `run_example(example_dir)` — Run a single example and return success status.
- `find_examples(examples_dir)` — Find all example directories with prefact.yaml.
- `main()` — Run all examples and show results.
- `add(a, b)` — Add two numbers.
- `get_user(user_id)` — Get user by ID.
- `process_data()` — Process data.
- `process_data()` — Process data.
- `process_data(data)` — Process some data.
- `format_timestamp(ts)` — Format a timestamp.
- `read_file(filepath)` — Read file contents.
- `process_data(data)` — Process some data.
- `format_timestamp(ts)` — Format a timestamp.
- `read_file(filepath)` — Read file contents.
- `greet(name, age)` — Greet someone.
- `format_data(data)` — Format data.
- `greet(name, age)` — Greet someone.
- `format_data(data)` — Format data.
- `process()` — Process with unsorted imports.
- `process()` — Process with unsorted imports.
- `process_data(data)` — Process data with debug prints.
- `calculate(a, b)` — Calculate with debug output.
- `process_data(data)` — Process data with debug prints.
- `calculate(a, b)` — Calculate with debug output.
- `process_users(users)` — Process user data with multiple issues.
- `generate_report(data)` — Generate a report.
- `main(name, email)` — Main CLI command.
- `admin()` — Admin commands.
- `users()` — List all users.
- `format_name(first, last)` — Format a full name.
- `validate_email(email)` — Validate email address.
- `helper_function(data)` — A helper function without type hints.
- `process_data(data)` — Process some data without return type annotation.
- `calculate_sum(numbers)` — Calculate sum without type hints.
- `process_data(data)` — Process some data.
- `calculate_sum(numbers)` — Calculate sum of numbers.
- `create_user(name, email)` — Create a new user.
- `load_users_from_file(filepath)` — Load users from JSON file.
- `run_prefact_example(project_path, config_file, dry_run)` — Run prefact on a project and display results.
- `custom_rule_example()` — Example of using prefact with custom rules.
- `batch_processing_example()` — Example of processing multiple projects.
- `main()` — Main entry point.
- `install_git_hooks(repo_root)` — Install Git hooks for the current repository.
- `uninstall_git_hooks(repo_root)` — Uninstall Git hooks for the current repository.
- `list_git_hooks(repo_root)` — List status of Git hooks.
- `main()` — Main CLI for Git hooks management.
- `process()` — Process using wildcard imports.
- `process()` — Process using wildcard imports.
- `main(ctx, autonomous, init_only, skip_tests)` — prefact – automatic Python prefactoring toolkit.
- `scan()` — Scan for issues without applying fixes.
- `fix(dry_run, no_backup)` — Scan, fix, and validate in one pass.
- `check(filepath)` — Scan a single file.
- `init(project_path)` — Generate a default prefact.yaml in the project directory.
- `autonomous_cmd(project_path, init_only, skip_tests, skip_examples)` — Run autonomous prefact mode (-a).
- `rules()` — List all available rules.
- `initialize_cache(config)` — Initialize the cache system.
- `get_cache()` — —
- `get_scan_cache()` — —
- `get_config_cache()` — —
- `get_rule_cache()` — —
- `get_hash_cache()` — —
- `close_cache()` — —
- `get_plugin_manager(config)` — Get the global plugin manager instance.
- `register_plugin_rule(plugin_name, version)` — Decorator to register a rule as part of a plugin.
- `init_worker()` — Initialize worker process.
- `scan_file_worker(args)` — Worker function for scanning a single file.
- `get_performance_monitor()` — Get the global performance monitor.
- `print_report(result)` — —
- `initialize_cache(config)` — Initialize the cache system.
- `get_cache()` — Get the global cache instance.
- `get_scan_cache()` — Get the scan result cache.
- `get_config_cache()` — Get the configuration cache.
- `get_rule_cache()` — Get the rule result cache.
- `get_hash_cache()` — Get the file hash cache.
- `cleanup_cache()` — Clean up cache resources.
- `cached_result(expire, key_func)` — Decorator to cache function results.
- `cached_file_operation(expire)` — Decorator to cache file operations.
- `clear_cache(pattern)` — Clear cache entries matching pattern.
- `get_cache_info()` — Get comprehensive cache information.
- `to_dict(result)` — —
- `dump(result)` — —
- `deep_merge(base, override)` — —
- `register_composite_rules(config)` — Register composite rules defined in configuration.
- `generate_pylint_rc(config, output_path)` — Generate a .pylintrc file based on prefact configuration.
- `get_lazy_registry()` — Get the global lazy rule registry.
- `get_all_rules()` — Get all rule classes (loads them all).
- `get_rule(rule_id)` — Get a rule class by ID.
- `register(rule_class)` — Decorator to register a rule class.
- `register(cls)` — Decorator that registers a rule class.
- `get_all_rules()` — Get all registered rule classes (loads them all).
- `get_rule(rule_id)` — Get a rule class by ID (loads it if necessary).
- `parse_cached(source)` — Return cached ast.Module for *source*, parsing it on first call.
- `clear()` — Evict all entries – call after fixing a file to avoid stale trees.
- `generate_import_linter_config(config, output_path)` — Generate a comprehensive import-linter configuration.
- `build_prefact_suite()` — —
- `benchmark_library(module, cli_commands, test_path, threshold_import)` — Generic helper to benchmark *any* installed Python library.
- `main()` — —
- `benchmark_file(file_path, config)` — Benchmark a single file with both AST and Ruff implementations.
- `benchmark_project(project_root, config)` — Benchmark entire project.
- `print_benchmark_results(results)` — Print formatted benchmark results.
- `main()` — Run benchmark on current project.
- `add_ruff_config_to_prefact_yaml(config_path)` — Add Ruff-specific configuration to prefact.yaml.


## Project Structure

📄 `benchmark_ram_optimization` (5 functions)
📄 `examples.01-individual-rules.duplicate-imports.after` (1 functions)
📄 `examples.01-individual-rules.duplicate-imports.before` (1 functions)
📄 `examples.01-individual-rules.missing-return-type.after` (3 functions, 1 classes)
📄 `examples.01-individual-rules.missing-return-type.before` (3 functions, 1 classes)
📄 `examples.01-individual-rules.print-statements.after` (2 functions)
📄 `examples.01-individual-rules.print-statements.before` (2 functions)
📄 `examples.01-individual-rules.relative-imports.after` (3 functions, 1 classes)
📄 `examples.01-individual-rules.relative-imports.before` (3 functions, 1 classes)
📄 `examples.01-individual-rules.sorted-imports.after` (1 functions)
📄 `examples.01-individual-rules.sorted-imports.before` (1 functions)
📄 `examples.01-individual-rules.string-concat.after` (2 functions)
📄 `examples.01-individual-rules.string-concat.before` (2 functions)
📄 `examples.01-individual-rules.unused-imports.after` (6 functions, 1 classes)
📄 `examples.01-individual-rules.unused-imports.before` (6 functions, 1 classes)
📄 `examples.01-individual-rules.wildcard-imports.after` (1 functions)
📄 `examples.01-individual-rules.wildcard-imports.before` (1 functions)
📄 `examples.02-multiple-rules.messy_module` (4 functions, 1 classes)
📄 `examples.03-output-formats.sample_code` (2 functions)
📦 `examples.04-custom-rules.custom_rules`
📄 `examples.04-custom-rules.custom_rules.no_todo_rule` (7 functions, 2 classes)
📄 `examples.06-api-usage.example` (4 functions)
📄 `examples.generate_examples`
📄 `examples.run_all` (3 functions)
📄 `examples.run_examples` (3 functions)
📄 `examples.sample-project.cli` (3 functions)
📄 `examples.sample-project.core` (5 functions, 1 classes)
📄 `examples.sample-project.models` (5 functions, 2 classes)
📄 `examples.sample-project.utils` (5 functions, 1 classes)
📄 `project`
📦 `src.prefact`
📄 `src.prefact._base`
📦 `src.prefact.autonomous` (16 functions, 1 classes)
📄 `src.prefact.autonomous._base` (1 functions, 1 classes)
📄 `src.prefact.autonomous.dependency_checker` (11 functions, 1 classes)
📄 `src.prefact.autonomous.docs_manager` (6 functions, 1 classes)
📄 `src.prefact.autonomous.project_scanner` (7 functions, 1 classes)
📄 `src.prefact.autonomous.setup_manager` (3 functions, 1 classes)
📄 `src.prefact.autonomous.todo_manager` (14 functions, 1 classes)
📄 `src.prefact.benchmark` (6 functions, 1 classes)
📄 `src.prefact.cli` (10 functions)
📄 `src.prefact.config` (13 functions, 2 classes)
📦 `src.prefact.config_extended`
📄 `src.prefact.config_extended.config` (8 functions, 1 classes)
📄 `src.prefact.config_extended.constants`
📄 `src.prefact.config_extended.generator` (3 functions, 1 classes)
📄 `src.prefact.config_extended.models` (3 functions, 1 classes)
📄 `src.prefact.config_extended.utils` (1 functions)
📄 `src.prefact.config_extended.validation` (6 functions, 1 classes)
📄 `src.prefact.config_extended.validators` (4 functions, 1 classes)
📄 `src.prefact.engine` (5 functions, 1 classes)
📄 `src.prefact.fixer` (3 functions, 1 classes)
📄 `src.prefact.git_hooks` (17 functions, 2 classes)
📦 `src.prefact.logging`
📄 `src.prefact.logging.exceptions` (3 functions, 4 classes)
📄 `src.prefact.logging.formatters` (1 functions, 1 classes)
📄 `src.prefact.logging.levels` (1 classes)
📄 `src.prefact.logging.logger` (15 functions, 2 classes)
📄 `src.prefact.models` (6 classes)
📦 `src.prefact.performance`
📄 `src.prefact.performance.cache` (37 functions, 6 classes)
📄 `src.prefact.performance.cache_adapters` (16 functions, 4 classes)
📄 `src.prefact.performance.cache_state` (7 functions)
📄 `src.prefact.performance.parallel` (23 functions, 4 classes)
📦 `src.prefact.plugins` (17 functions, 3 classes)
📄 `src.prefact.plugins.builtin`
📦 `src.prefact.reporters`
📄 `src.prefact.reporters.console` (1 functions)
📄 `src.prefact.reporters.json_reporter` (2 functions)
📦 `src.prefact.rules` (7 functions, 1 classes)
📄 `src.prefact.rules._ast_cache` (2 functions)
📄 `src.prefact.rules.ai_boilerplate` (3 functions, 1 classes)
📄 `src.prefact.rules.autoflake_based` (23 functions, 5 classes)
📄 `src.prefact.rules.benchmark` (4 functions)
📄 `src.prefact.rules.composite_factory` (2 functions, 1 classes)
📄 `src.prefact.rules.composite_rules` (16 functions, 3 classes)
📄 `src.prefact.rules.duplicate_imports` (3 functions, 1 classes)
📄 `src.prefact.rules.import_linter_based` (24 functions, 5 classes)
📄 `src.prefact.rules.importchecker_based` (24 functions, 5 classes)
📄 `src.prefact.rules.isort_based` (23 functions, 4 classes)
📄 `src.prefact.rules.llm_generated_code` (9 functions, 1 classes)
📄 `src.prefact.rules.llm_hallucinations` (9 functions, 1 classes)
📄 `src.prefact.rules.magic_numbers` (6 functions, 1 classes)
📄 `src.prefact.rules.migration` (10 functions, 3 classes)
📄 `src.prefact.rules.mypy_based` (22 functions, 6 classes)
📄 `src.prefact.rules.print_statements` (3 functions, 1 classes)
📄 `src.prefact.rules.pylint_based` (22 functions, 5 classes)
📄 `src.prefact.rules.registry` (13 functions, 1 classes)
📄 `src.prefact.rules.relative_imports` (9 functions, 2 classes)
📄 `src.prefact.rules.ruff_based` (19 functions, 6 classes)
📄 `src.prefact.rules.sorted_imports` (4 functions, 1 classes)
📄 `src.prefact.rules.strategies` (10 functions, 4 classes)
📄 `src.prefact.rules.string_concat` (5 functions, 1 classes)
📄 `src.prefact.rules.string_transformations` (27 functions, 6 classes)
📄 `src.prefact.rules.type_hints` (3 functions, 1 classes)
📄 `src.prefact.rules.unimport_based` (22 functions, 5 classes)
📄 `src.prefact.rules.unused_imports` (11 functions, 1 classes)
📄 `src.prefact.rules.wildcard_imports` (3 functions, 1 classes)
📄 `src.prefact.scanner` (7 functions, 1 classes)
📄 `src.prefact.validator` (2 functions, 1 classes)
📄 `vscode-extension.src.extension` (58 functions, 5 classes)

## Requirements

- Python >= >=3.8
- ast-decompiler >=0.7.0- click >=8.0.0- libcst >=0.4.0- pyyaml >=6.0- rich >=12.0.0- tomli >=2.0.0; python_version<'3.11'- goal >=2.1.0- costs >=0.1.20- pfix >=0.1.60

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/semcod/refactoring
cd prefact

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 📖 [Full Documentation](https://github.com/semcod/refactoring/tree/main/docs) — API reference, module docs, architecture
- 🚀 [Getting Started](https://github.com/semcod/refactoring/blob/main/docs/getting-started.md) — Quick start guide
- 📚 [API Reference](https://github.com/semcod/refactoring/blob/main/docs/api.md) — Complete API documentation
- 🔧 [Configuration](https://github.com/semcod/refactoring/blob/main/docs/configuration.md) — Configuration options
- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/api.md` | Consolidated API reference | [View](./docs/api.md) |
| `docs/modules.md` | Module reference with metrics | [View](./docs/modules.md) |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |
| `docs/dependency-graph.md` | Dependency graphs | [View](./docs/dependency-graph.md) |
| `docs/coverage.md` | Docstring coverage report | [View](./docs/coverage.md) |
| `docs/getting-started.md` | Getting started guide | [View](./docs/getting-started.md) |
| `docs/configuration.md` | Configuration reference | [View](./docs/configuration.md) |
| `docs/api-changelog.md` | API change tracking | [View](./docs/api-changelog.md) |
| `CONTRIBUTING.md` | Contribution guidelines | [View](./CONTRIBUTING.md) |
| `examples/` | Usage examples | [Browse](./examples) |
| `mkdocs.yml` | MkDocs configuration | — |

<!-- code2docs:end -->