# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed — rule_id collision architecture (breaking config change)
- **Root cause**: 7 groups of rule classes (`sorted-imports`, `string-concat`,
  `unused-imports`, `duplicate-imports`, `wildcard-imports`, `print-statements`,
  `missing-return-type`) silently shared a bare `rule_id` across their AST-only
  and tool-backed (ruff/isort/mypy/pylint/autoflake/unimport/importchecker)
  implementations. `@register` just overwrites `_rule_cache[rule_id]`, so
  whichever module `prefact/rules/__init__.py` happened to import *last* won —
  an unlabeled, import-order-dependent choice with zero user-facing way to
  select an implementation (the `migration.py`/`MIGRATION_MAP` mechanism that
  looked like it should govern this was confirmed dead code, never wired into
  the runtime pipeline). Concretely, e.g. `SortedImports` (dependency-free,
  detect-only, deliberately delegates fixing "to isort/ruff") was completely
  unreachable — always shadowed by whichever backend-specific class imported
  last.
- **Fix**: every backend-specific class now has its own namespaced `rule_id`
  — `ruff-sorted-imports`, `isorted-imports`, `pylint-string-concat`,
  `autoflake-unused-imports`, `unimport-duplicate-imports`,
  `importchecker-unused-imports`, `mypy-missing-return-type`, etc. These were
  already the exact keys `LazyRuleRegistry._rule_modules` expected for these
  modules (evidence the namespacing scheme was the original intent; the class
  attributes just never got updated to match). The AST-only canonical rule in
  each group keeps its own `ast-`-prefixed id (`ast-sorted-imports`,
  `ast-unused-imports`, ...) instead of the bare name, for naming symmetry
  with its now-independent siblings. All are independently selectable via the
  existing `rules:` section in `prefact.yaml` (`config.rule_enabled(rule_id)`)
  — no new mechanism needed, just real, unique identities. Also updated same-
  package cross-references that read a sibling's config by the old bare id
  (`isort_based/section_separator.py`, `string_transformations/
  context_aware_concat.py`) and `composite_rules.py`'s `tool_priorities` dict
  (which matches issues by literal `rule_id`, unlike its `is_rule_enabled(...)`
  family-level toggles, which needed no change since they're free-standing
  config keys, not rule identities).
- **Migration**: any existing `prefact.yaml` with a `rules:` entry keyed by one
  of the old bare ids (`sorted-imports`, `string-concat`, `unused-imports`,
  `duplicate-imports`, `wildcard-imports`, `print-statements`,
  `missing-return-type`) now targets a nonexistent rule id and silently has no
  effect — rename it to `ast-<name>` (or to the specific backend id you meant)
  to keep prior behavior.
- **Fixed `get_all_rules()`** (`registry.py`, used by `scanner.py`/`fixer.py`/
  `validator.py`/`prefact rules`): it iterated only `LazyRuleRegistry.
  _rule_modules`'s keys — a static dict with several stale entries (module
  paths pointing at files that don't exist, e.g. `prefact.rules.composite`
  instead of the real `composite_rules.py`) and missing keys entirely for
  others (`unused-variables`, `no-relative-imports`, ...). Now also merges in
  `_rule_cache` (every class actually registered via `@register` at import
  time — ground truth). `get_all_rules()` went from surfacing ~21 of the ~46
  actually-registered rules to all of them.
- **Adjacent bugs this uncovered** (both previously unreachable, now
  instantiated by the fixed `get_all_rules()`, so both had to be fixed for the
  full test suite / a real scan to pass):
  - `AutoflakeUnusedVariables` (`autoflake_based.py`) was missing its
    `scan_file`/`fix`/`validate` implementations entirely — an abstract,
    uninstantiable stub. Restored the complete implementation (recovered from
    a stray `autoflake_based.py.bak` in the same directory).
  - `ImportDependencyAnalysis.scan_file` (`importchecker_based.py`) did
    `imp.count(".")` where `imp` is a `dict` (`{"name": ..., "line": ...}`),
    raising `AttributeError` on every file with any import — fixed to
    `imp["name"].count(".")`, matching the same loop's other accesses.
- **Verified**: `tests/test_rule_registry.py` (new) asserts the 7 previously-
  colliding groups resolve to their intended classes, that no two live
  (non-`.bak`) classes share a `rule_id` literal, and that `get_all_rules()`
  surfaces ids absent from `_rule_modules`. Ran `prefact rules` (CLI listing,
  now shows 46 rules, up from ~21, no instantiation errors) and `prefact
  check` against a real multi-issue file end-to-end. Full test suite (98
  tests with `isort`/`diskcache` installed, 96 + 2 correctly skipped without)
  passes.

### Changed
- Reduced `TestQLManager.run`'s cyclomatic complexity (flagged CC=15, at the
  project's own limit) by extracting the ticket-creation/upsert/sync block
  into `_create_and_sync_tickets`. No behavior change; existing
  `tests/test_testql_manager.py` (7 tests) passes unmodified.

### Fixed
- `DocsManager.update_changelog_md` (autonomous mode) hardcoded `version = "0.1.10"`
  for every changelog entry it wrote, regardless of the actual target project's
  version — this is the direct cause of the many duplicate `## [0.1.10] - <date>`
  headers scattered through this very CHANGELOG.md's history at six different
  dates. Added `_detect_project_version()`, which reads `[project].version` from
  the target project's own `pyproject.toml` (falling back to `"Unreleased"`,
  never a stale placeholder, when the file or field is missing).
  Verified with `tests/test_docs_manager.py` (new file, 0 prior coverage):
  version detection with/without pyproject.toml/version field, and that
  `update_changelog_md` writes the detected version instead of `0.1.10`.

### Changed
- Reduced `DocsManager.update_planfile`'s cyclomatic complexity (flagged CC=27,
  the module's `code2llm` "layer hotspot") by extracting three focused private
  methods: `_remove_obsolete_tickets`, `_collect_new_tickets`,
  `_insert_new_tickets` — same logic, no behavior change. Verified with 5 new
  tests covering ticket creation, cross-issue-group dedup, obsolete-ticket
  cleanup on re-run, and the `autonomous_max_tickets` limit.
- Split `src/prefact/rules/string_transformations.py` (501 lines, 6 classes) into a
  package of three transformer+rule pairs: `string_concat.py`
  (`StringConcatTransformer`/`StringConcatToFString`), `flynt_formatting.py`
  (`FlyntHelper`/`FlyntStringFormatting`), `context_aware_concat.py`
  (`ContextAwareStringTransformer`/`ContextAwareStringConcat`, which imports from
  `string_concat` — preserved as a submodule import). `__init__.py` re-exports every
  original name and eagerly imports every submodule so `@register` still fires.
  Verified end-to-end (scan/fix/validate on real string-concatenation and
  `.format()`/`%`-formatting source) for all three rule classes; full test suite
  (85 passed, 2 correctly skipped) passes.
- Split `src/prefact/rules/isort_based.py` (519 lines, 4 classes) into a package
  (`isort_based/{helper,sorted_imports,section_separator,custom_organization}.py`)
  with `__init__.py` re-exporting every original name (including `HAS_ISORT`) and
  eagerly importing every rule submodule so their `@register` decorators still
  fire on package import. Also removed a duplicated `if not HAS_ISORT: return []`
  check in `ISortedImports.scan_file` found while porting it (dead, harmless, but
  no reason to carry it forward).
  Verified: all four classes exercised end-to-end with `isort` actually installed
  (scan/fix/validate on real unsorted source) in addition to the `HAS_ISORT=False`
  fallback path; full test suite (86 tests with isort installed, 85 + 2 skipped
  without) passes either way.

### Fixed
- `prefact.performance` was completely unimportable (`ImportError: cannot import
  name 'CacheContext' from 'prefact.performance.cache'`): an in-progress refactor
  from a flat `cache.py` to a `cache/` package had left `cache.py` and `cache_state.py`
  as orphaned, unreferenced files — `cache.py` collided with the new `cache/` package's
  name (Python resolved to the package, shadowing the old module), and `cache_state.py`
  imported a nonexistent `.cache_core` module. Neither file was imported by anything else
  in the codebase (confirmed via full-repo grep), so this had gone unnoticed. Completed
  the refactor: ported the six names the old `cache.py` had that `cache/__init__.py`
  didn't yet re-export (`CacheContext`, `cleanup_cache`, `clear_cache`, `get_config_cache`,
  `get_hash_cache`, `get_rule_cache`) into `cache/globals.py` using the new package's
  `Cache` class (same API surface: `.get`/`.set`/`.delete`/`.clear`/`.close`), then
  deleted both orphaned files. Added `tests/test_performance_cache.py` (previously zero
  test coverage existed for this subpackage) — an import-surface test that runs
  unconditionally (the regression needed no diskcache instance, just the names to
  resolve) plus a `CacheContext` lifecycle test gated on `pytest.importorskip("diskcache")`
  since it's an optional extra. Full test suite (85 tests, 2 correctly skipped) passes.
- `DEFAULT_EXCLUDE` used prefix globs (`**/.venv*/**`, `**/venv*/**`) and the scanner's
  hardcoded fallback used `part.startswith("venv")` / `part.startswith(".venv")`, matching
  any directory component that merely starts with those names (e.g. a real `venv_utils/` or
  `environment/` source directory), silently dropping it from analysis. Replaced with exact
  directory-name matches (`venv`, `.venv`, `env`, `.env`, `virtualenv`, `site-packages`).
- `Scanner.collect_files()` used `root.glob(pattern)`, which fully traverses the tree
  (stat'ing every file inside a populated virtualenv) before exclusion patterns are applied.
  Rewrote to walk with `os.walk` and prune excluded directories before descending into them.

## [0.1.67] - 2026-07-05

### Docs
- Update CHANGELOG.md
- Update README.md

### Test
- Update tests/test_rule_registry.py

### Other
- Update .planfile/sprints/current.yaml

## [0.1.66] - 2026-07-05

### Docs
- Update CHANGELOG.md
- Update README.md

### Other
- Update .planfile/sprints/current.yaml

## [0.1.65] - 2026-07-05

### Docs
- Update CHANGELOG.md
- Update README.md

### Test
- Update tests/test_docs_manager.py

### Other
- Update .planfile/sprints/current.yaml

## [0.1.64] - 2026-07-05

### Docs
- Update CHANGELOG.md
- Update README.md

### Other
- Update .planfile/sprints/current.yaml

## [0.1.63] - 2026-07-05

### Docs
- Update CHANGELOG.md
- Update README.md

### Other
- Update .planfile/sprints/current.yaml

## [0.1.62] - 2026-07-05

### Docs
- Update CHANGELOG.md
- Update README.md

### Test
- Update tests/test_performance_cache.py

### Other
- Update .planfile/sprints/current.yaml

## [0.1.61] - 2026-07-05

### Docs
- Update README.md

### Other
- Update .gitignore
- Update .planfile/.koru/nfo-events.jsonl
- Update .planfile/.koru/operator-steps/mcp_koru.ticket
- Update .planfile/.koru/queue-runner.lock
- Update project/planfile-tickets.yaml

## [0.1.60] - 2026-07-05

### Docs
- Update CHANGELOG.md
- Update README.md

### Test
- Update tests/test_config.py

### Other
- Update local.dev.txt
- Update vscode-extension/local.dev.txt

## [0.1.10] - 2026-05-24

### Fixed
- Fix smart-return-type issues (ticket-44e99cb5)
- Fix magic-numbers issues (ticket-916b11ef)
- Fix unused-imports issues (ticket-b16c9759)
- Fix magic-numbers issues (ticket-eb4c68d9)
- Fix magic-numbers issues (ticket-3107a1ca)
- Fix unused-imports issues (ticket-2003de2f)
- Fix string-concat issues (ticket-fb914fa8)
- Fix string-concat issues (ticket-5bc52af6)
- Fix relative-imports issues (ticket-4339cea3)
- Fix relative-imports issues (ticket-b559e532)
- Fix relative-imports issues (ticket-4e5eebbd)
- Fix relative-imports issues (ticket-1af40d56)
- Fix string-concat issues (ticket-fa84f94a)
- Fix relative-imports issues (ticket-51807278)
- Fix magic-numbers issues (ticket-83c9d2ab)
- Fix smart-return-type issues (ticket-9eea52d4)
- Fix string-concat issues (ticket-2629eaca)
- Fix llm-hallucinations issues (ticket-a797648c)
- Fix smart-return-type issues (ticket-52920e08)
- Fix smart-return-type issues (ticket-f5df4b3b)
- Fix string-concat issues (ticket-7275ac50)
- Fix ai-boilerplate issues (ticket-fe0f0bc7)
- Fix smart-return-type issues (ticket-de7212b0)
- Fix llm-hallucinations issues (ticket-a8b4f10e)

## [0.1.10] - 2026-04-25

### Fixed
- Fix relative-imports issues (ticket-8920ec64)
- Fix magic-numbers issues (ticket-02dc0d73)
- Fix ai-boilerplate issues (ticket-b38b2991)
- Fix magic-numbers issues (ticket-29beceb4)
- Fix string-concat issues (ticket-2334c68e)
- Fix duplicate-imports issues (ticket-028f9b29)
- Fix magic-numbers issues (ticket-c7c61163)

## [0.1.10] - 2026-03-27

### Fixed
- Fix unused-imports issues (ticket-c0e4d079)
- Fix magic-numbers issues (ticket-29beceb4)
- Fix relative-imports issues (ticket-8920ec64)
- Fix unused-imports issues (ticket-2d98e168)
- Fix relative-imports issues (ticket-9801b62d)
- Fix relative-imports issues (ticket-04bf7323)
- Fix string-concat issues (ticket-d4263e88)
- Fix relative-imports issues (ticket-cb48b598)
- Fix unused-imports issues (ticket-84838c10)
- Fix relative-imports issues (ticket-1895af28)
- Fix string-concat issues (ticket-0b11f372)
- Fix duplicate-imports issues (ticket-ae96df0a)
- Fix relative-imports issues (ticket-5d99b02e)

## [0.1.10] - 2026-03-27

### Fixed
- Fix magic-numbers issues (ticket-324f7c1c)

## [0.1.10] - 2026-03-27

### Fixed
- Fix wildcard-imports issues (ticket-f59adb71)
- Fix wildcard-imports issues (ticket-e0342587)
- Fix wildcard-imports issues (ticket-f50ed65e)

## [0.1.10] - 2026-03-27

### Fixed
- Fix duplicate-imports issues (ticket-49d37755)

## [0.1.10] - 2026-03-27

### Fixed
- Fix smart-return-type issues (ticket-7adcbb2b)
- Fix string-concat issues (ticket-242b0517)
- Fix unused-imports issues (ticket-de239fa7)
- Fix magic-numbers issues (ticket-02dc0d73)
- Fix ai-boilerplate issues (ticket-b38b2991)
- Fix llm-generated-code issues (ticket-b3a94431)
- Fix smart-return-type issues (ticket-e338c3a9)
- Fix string-concat issues (ticket-133af5e9)
- Fix ai-boilerplate issues (ticket-054d6766)

## [0.1.22] - 2026-03-27

### Added
- Parallel processing support for faster scanning (configurable max_workers)
- Smart file filtering to skip large files (>100KB) and empty files
- Autonomous mode header with version information
- Deduplication logic for TODO.md and planfile.yaml tickets

### Changed
- Removed deprecated `print-statement` rule from pylint configuration
- Optimized exclude patterns to include test directories and examples
- Updated header display to be more compact

### Fixed
- Escape sequence issues in f-strings causing Python 3.8 compatibility errors
- Duplicate ticket creation within the same run
- Unused imports across multiple modules (cli.py, logging.py, plugins, rules)
- String concatenation issues converted to f-strings

### Code Cleanup
- Removed unused `from __future__ import annotations` from multiple files
- Cleaned up unused imports (json, shutil, os, pickle, etc.)
- Removed duplicate imports in autoflake_based.py and unimport_based.py
- Simplified type annotations by removing unused Union imports

## [0.1.10] - 2026-03-27

### Fixed
- Fix wildcard-imports issues (ticket-eddf6c3b)
- Fix magic-numbers issues (ticket-3e1f69d6)

## [0.1.10] - 2026-03-27

### Fixed
- Fix print-statements issues (ticket-6d9734af)
- Fix print-statements issues (ticket-795ea948)
- Fix print-statements issues (ticket-fece0ed9)
- Fix print-statements issues (ticket-757cb576)
- Fix print-statements issues (ticket-a9f2d25a)
- Fix print-statements issues (ticket-3200084a)
- Fix print-statements issues (ticket-f60ee670)
- Fix print-statements issues (ticket-c3f4716c)
- Fix print-statements issues (ticket-e548d604)
- Fix print-statements issues (ticket-e2222289)
- Fix print-statements issues (ticket-fc637bc5)
- Fix print-statements issues (ticket-2fa3e811)
- Fix print-statements issues (ticket-4cb672d3)
- Fix print-statements issues (ticket-a878d687)
- Fix print-statements issues (ticket-df7df4bf)
- Fix print-statements issues (ticket-9569e7a8)
- Fix print-statements issues (ticket-b05d4c89)
- Fix print-statements issues (ticket-c0f9550b)
- Fix print-statements issues (ticket-14c47fd3)
- Fix print-statements issues (ticket-acbb7841)
- Fix print-statements issues (ticket-48264d64)
- Fix print-statements issues (ticket-e7625bb7)
- Fix print-statements issues (ticket-686e96f8)
- Fix print-statements issues (ticket-c82c5990)
- Fix print-statements issues (ticket-a22fd598)
- Fix print-statements issues (ticket-7ce27c3e)
- Fix print-statements issues (ticket-7be9d520)
- Fix print-statements issues (ticket-79bcc9dd)
- Fix print-statements issues (ticket-6454bdff)
- Fix print-statements issues (ticket-768aac28)
- Fix print-statements issues (ticket-2f49542e)
- Fix print-statements issues (ticket-b2529fa3)
- Fix print-statements issues (ticket-2f1579b3)
- Fix print-statements issues (ticket-7223b67c)
- Fix print-statements issues (ticket-b80a85fb)
- Fix print-statements issues (ticket-0f492025)
- Fix print-statements issues (ticket-10492ac4)
- Fix print-statements issues (ticket-7a4239d5)
- Fix print-statements issues (ticket-a618f91f)
- Fix print-statements issues (ticket-fa9f7222)
- Fix print-statements issues (ticket-51e9c5a1)
- Fix print-statements issues (ticket-93495c2a)
- Fix print-statements issues (ticket-ec5d40e1)
- Fix print-statements issues (ticket-f9c1c389)
- Fix print-statements issues (ticket-fae31cac)
- Fix print-statements issues (ticket-e934a0e7)
- Fix print-statements issues (ticket-88915d9c)
- Fix print-statements issues (ticket-0aff9891)

## [0.1.10] - 2026-03-27

### Fixed
- Fix smart-return-type issues (ticket-474934b5)

## [0.1.10] - 2026-03-27

### Fixed
- Fix smart-return-type issues (ticket-e5c41121)
- Fix unused-imports issues (ticket-c7040878)
- Fix duplicate-imports issues (ticket-2cedfab5)
- Fix smart-return-type issues (ticket-335bf45a)
- Fix unused-imports issues (ticket-12f6d274)
- Fix smart-return-type issues (ticket-aa700792)
- Fix string-concat issues (ticket-9afae806)
- Fix smart-return-type issues (ticket-68301c01)
- Fix string-concat issues (ticket-d267051a)
- Fix smart-return-type issues (ticket-9e8194af)
- Fix string-concat issues (ticket-e2d80bc7)
- Fix smart-return-type issues (ticket-1ae4258d)
- Fix string-concat issues (ticket-bec2cb81)
- Fix wildcard-imports issues (ticket-a2e64792)
- Fix smart-return-type issues (ticket-4cef4c7a)
- Fix unused-imports issues (ticket-d2c3e43b)
- Fix relative-imports issues (ticket-c0780edb)
- Fix wildcard-imports issues (ticket-7aa3be91)
- Fix smart-return-type issues (ticket-87e8421d)
- Fix unused-imports issues (ticket-6ceca6cd)
- Fix relative-imports issues (ticket-9ee30c8e)
- Fix smart-return-type issues (ticket-7bd7e33c)
- Fix unused-imports issues (ticket-c8d2b79e)
- Fix relative-imports issues (ticket-cc0d8678)
- Fix smart-return-type issues (ticket-f45edd2b)
- Fix unused-imports issues (ticket-64105d2e)
- Fix smart-return-type issues (ticket-ae74ef07)
- Fix smart-return-type issues (ticket-91f8cb20)
- Fix string-concat issues (ticket-8f7076da)
- Fix unused-imports issues (ticket-42141651)
- Fix relative-imports issues (ticket-0f5d1f57)
- Fix duplicate-imports issues (ticket-f9a73874)
- Fix wildcard-imports issues (ticket-8fd5dae2)
- Fix smart-return-type issues (ticket-a9282a1f)
- Fix unused-imports issues (ticket-efb6b7e2)
- Fix relative-imports issues (ticket-00a3f06d)
- Fix duplicate-imports issues (ticket-55266c45)
- Fix wildcard-imports issues (ticket-dec18fad)
- Fix smart-return-type issues (ticket-436f3f9d)
- Fix unused-imports issues (ticket-a465f85b)
- Fix relative-imports issues (ticket-7b7ddd05)
- Fix smart-return-type issues (ticket-a3daf553)
- Fix string-concat issues (ticket-08d58ab6)
- Fix unused-imports issues (ticket-16e09896)
- Fix relative-imports issues (ticket-e0e2d8d3)
- Fix smart-return-type issues (ticket-7a0af27c)
- Fix string-concat issues (ticket-725a26b4)
- Fix unused-imports issues (ticket-c376c43d)
- Fix relative-imports issues (ticket-cefb0cd0)
- Fix smart-return-type issues (ticket-e54a5b66)
- Fix string-concat issues (ticket-70a06a1a)
- Fix unused-imports issues (ticket-174738fc)
- Fix llm-hallucinations issues (ticket-f3bf766d)
- Fix magic-numbers issues (ticket-ced904ab)
- Fix ai-boilerplate issues (ticket-3af627ed)
- Fix unused-imports issues (ticket-8b59d371)
- Fix smart-return-type issues (ticket-84cb419e)
- Fix unused-imports issues (ticket-278ef2b0)
- Fix ai-boilerplate issues (ticket-2dc37273)
- Fix relative-imports issues (ticket-abbade75)
- Fix smart-return-type issues (ticket-cecef1df)
- Fix string-concat issues (ticket-a7ba4dbb)
- Fix unused-imports issues (ticket-2de86a57)
- Fix ai-boilerplate issues (ticket-cbafd961)
- Fix wildcard-imports issues (ticket-e6121711)
- Fix smart-return-type issues (ticket-5a5bf7e1)
- Fix string-concat issues (ticket-15e3961b)
- Fix smart-return-type issues (ticket-697d9c38)
- Fix string-concat issues (ticket-3872e251)
- Fix smart-return-type issues (ticket-486ac306)
- Fix string-concat issues (ticket-d2629c69)
- Fix string-concat issues (ticket-8dcd309d)
- Fix unused-imports issues (ticket-d724da7f)
- Fix unused-imports issues (ticket-a7f2cee8)
- Fix duplicate-imports issues (ticket-a0b0d439)
- Fix ai-boilerplate issues (ticket-d7787f83)
- Fix unused-imports issues (ticket-c8c68ad9)
- Fix duplicate-imports issues (ticket-f1dc440b)
- Fix unused-imports issues (ticket-a125ae3a)
- Fix magic-numbers issues (ticket-743317da)
- Fix unused-imports issues (ticket-567f430c)
- Fix string-concat issues (ticket-2e3f5471)
- Fix unused-imports issues (ticket-f8c0c326)
- Fix smart-return-type issues (ticket-cb6e6df9)
- Fix unused-imports issues (ticket-cc6e4430)
- Fix ai-boilerplate issues (ticket-81d2165c)
- Fix smart-return-type issues (ticket-00517738)
- Fix unused-imports issues (ticket-6b47cff0)
- Fix unused-imports issues (ticket-7bd1f986)
- Fix smart-return-type issues (ticket-e6cf1eb3)
- Fix string-concat issues (ticket-38c5eb42)
- Fix unused-imports issues (ticket-12e03e69)
- Fix magic-numbers issues (ticket-53162289)
- Fix smart-return-type issues (ticket-9aa919bc)
- Fix string-concat issues (ticket-8142b3c5)
- Fix unused-imports issues (ticket-606216db)
- Fix duplicate-imports issues (ticket-7ee8f0ef)
- Fix smart-return-type issues (ticket-b2fb9f0b)
- Fix unused-imports issues (ticket-32e41cd5)
- Fix unused-imports issues (ticket-36c4092a)
- Fix string-concat issues (ticket-5bc52af6)
- Fix unused-imports issues (ticket-eb8d091c)
- Fix unused-imports issues (ticket-48240d17)
- Fix unused-imports issues (ticket-60197482)
- Fix ai-boilerplate issues (ticket-7a5bf382)
- Fix unused-imports issues (ticket-e6c1f103)
- Fix duplicate-imports issues (ticket-1f499a4a)
- Fix smart-return-type issues (ticket-a3166b4a)
- Fix string-concat issues (ticket-4f278902)
- Fix unused-imports issues (ticket-68ac49fc)
- Fix ai-boilerplate issues (ticket-05c02e79)
- Fix unused-imports issues (ticket-facaf445)
- Fix unused-imports issues (ticket-0a68ccfd)
- Fix unused-imports issues (ticket-13ac6579)
- Fix unused-imports issues (ticket-7734659e)
- Fix duplicate-imports issues (ticket-3d5a1915)
- Fix string-concat issues (ticket-2f2a9221)
- Fix unused-imports issues (ticket-7d58a4b6)
- Fix string-concat issues (ticket-131fbc36)
- Fix unused-imports issues (ticket-458db142)
- Fix magic-numbers issues (ticket-2f8b17e3)
- Fix unused-imports issues (ticket-dad85add)
- Fix unused-imports issues (ticket-8aa902e0)
- Fix llm-hallucinations issues (ticket-f64489cc)
- Fix unused-imports issues (ticket-277e8b8f)
- Fix smart-return-type issues (ticket-9f7d86b9)
- Fix unused-imports issues (ticket-8f1b147c)
- Fix unused-imports issues (ticket-257a5ae7)
- Fix duplicate-imports issues (ticket-e03eed7f)
- Fix unused-imports issues (ticket-56ef4f69)
- Fix smart-return-type issues (ticket-12ffcc71)
- Fix unused-imports issues (ticket-ee28bc63)
- Fix unused-imports issues (ticket-89cf2ac3)
- Fix string-concat issues (ticket-349127ce)
- Fix unused-imports issues (ticket-cde03f37)
- Fix llm-hallucinations issues (ticket-ba72d983)
- Fix unused-imports issues (ticket-34a2bf6e)
- Fix unused-imports issues (ticket-0fbf05e2)
- Fix magic-numbers issues (ticket-238dae90)
- Fix unused-imports issues (ticket-570b6e00)
- Fix string-concat issues (ticket-aa92c01c)
- Fix unused-imports issues (ticket-99263596)
- Fix smart-return-type issues (ticket-22e7fcbf)
- Fix unused-imports issues (ticket-7c04a88f)
- Fix magic-numbers issues (ticket-83c9d2ab)
- Fix unused-imports issues (ticket-ac97ab7a)
- Fix string-concat issues (ticket-9508f720)
- Fix unused-imports issues (ticket-76cb20e3)
- Fix duplicate-imports issues (ticket-0c3365f2)
- Fix string-concat issues (ticket-fa84f94a)
- Fix unused-imports issues (ticket-7a513113)
- Fix unused-imports issues (ticket-9300959f)
- Fix string-concat issues (ticket-ace03dcb)
- Fix unused-imports issues (ticket-d5b7fa6d)
- Fix unused-imports issues (ticket-c1ba2cf8)

## [Unreleased]


- feat(docs): add Markdown output and update changelog generation
- feat(examples): add deep code analysis engine example with supporting modules
- feat(config): update configuration docs and CLI improvements
- refactor(docs): large refactor of the code analysis engine and CLI/interface improvements
- refactor: configuration management system improvements and duplicate-class removal
- fix: add type: ignore comments to suppress mypy errors in parallel.py
- fix: auto-fix ruff formatting issues and add missing imports
- chore(docs): update README and other documentation

## [0.1.59] - 2026-06-29

### Docs
- Update README.md

## [0.1.58] - 2026-05-24

### Docs
- Update README.md

### Test
- Update tests/test_config.py

### Other
- Update prefact.yaml
- Update uv.lock

## [0.1.56] - 2026-05-03

### Docs
- Update README.md

### Test
- Update tests/test_autonomous_limits.py
- Update tests/test_config.py
- Update tests/test_dependency_checker.py
- Update tests/test_engine.py
- Update tests/test_integrations.py
- Update tests/test_relative_imports.py
- Update tests/test_rules.py
- Update tests/test_testql_manager.py
- Update tests/test_unused_imports.py

## [0.1.55] - 2026-05-03

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Other
- Update app.doql.less
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- ... and 7 more files

## [0.1.54] - 2026-04-26

### Docs
- Update README.md

## [0.1.53] - 2026-04-26

### Docs
- Update README.md

### Test
- Update tests/test_testql_manager.py

## [0.1.52] - 2026-04-26

### Docs
- Update README.md

## [0.1.51] - 2026-04-26

### Docs
- Update README.md

### Test
- Update tests/test_testql_manager.py

## [0.1.50] - 2026-04-26

### Docs
- Update README.md

## [0.1.49] - 2026-04-26

### Docs
- Update CHANGELOG.md
- Update README.md

### Other
- Update .taskill/state.json
- Update planfile.yaml

## [0.1.48] - 2026-04-25

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- ... and 6 more files

## [0.1.47] - 2026-04-25

### Docs
- Update README.md

## [0.1.46] - 2026-04-25

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql-scenarios/generated-cli-tests.testql.toon.yaml
- Update testql-scenarios/generated-from-pytests.testql.toon.yaml

### Other
- Update app.doql.less
- Update planfile.yaml
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- ... and 9 more files

## [0.1.45] - 2026-04-25

### Docs
- Update README.md
- Update redsl_refactor_plan.md

### Other
- Update .gitignore
- Update .redsl/history.jsonl
- Update planfile.yaml
- Update redsl.yaml
- Update redsl_refactor_plan.toon.yaml

## [0.1.44] - 2026-04-20

### Docs
- Update README.md

### Other
- Update .redsl/history.jsonl
- Update planfile.yaml
- Update src/prefact/rules/ai_boilerplate.py.bak

## [0.1.43] - 2026-04-19

### Docs
- Update README.md
- Update redsl_refactor_plan.md
- Update redsl_refactor_report.md

### Other
- Update .redsl/history.jsonl
- Update Makefile
- Update planfile.yaml
- Update redsl_refactor_plan.toon.yaml
- Update redsl_refactor_report.toon.yaml

## [0.1.42] - 2026-04-19

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update docs/MIGRATION_GUIDE.md
- Update docs/RAM_OPTIMIZATION.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update project/root/context.md
- Update project/src_examples/context.md

### Other
- Update .redsl/history.jsonl
- Update Taskfile.yml
- Update app.doql.css
- Update project/analysis.toon.yaml
- Update project/evolution.toon.yaml
- Update project/index.html
- Update project/project.toon.yaml
- Update project/prompt.txt
- Update project/root/analysis.toon.yaml
- Update project/root/evolution.toon.yaml
- ... and 3 more files

## [0.1.41] - 2026-04-09

### Docs
- Update README.md

### Test
- Update tests/test_autonomous_limits.py

## [0.1.40] - 2026-04-09

### Docs
- Update README.md

### Test
- Update tests/test_autonomous_limits.py

## [0.1.39] - 2026-04-09

### Docs
- Update README.md

### Test
- Update tests/test_autonomous_limits.py

## [0.1.38] - 2026-04-09

### Docs
- Update README.md

### Test
- Update tests/test_autonomous_limits.py

## [0.1.37] - 2026-04-09

### Docs
- Update README.md

## [0.1.36] - 2026-04-09

### Docs
- Update README.md
- Update TODO.md

### Test
- Update tests/test_integrations.py

## [0.1.35] - 2026-04-09

### Docs
- Update README.md

## [0.1.34] - 2026-04-09

### Docs
- Update README.md

## [0.1.33] - 2026-04-09

### Docs
- Update README.md

## [0.1.32] - 2026-04-09

### Docs
- Update README.md

### Other
- Update .gitignore
- Update project/validation.toon.yaml
- Update vscode-extension/out/extension.js
- Update vscode-extension/out/extension.js.map
- Update vscode-extension/src/extension.ts

## [0.1.31] - 2026-04-09

### Docs
- Update BENCHMARK.md
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_dependency_checker.py
- Update tests/test_integrations.py

### Other
- Update .gitignore
- Update .pyqual/benchmark.json
- Update .pyqual/benchmark.txt
- Update .pyqual/coverage.json
- Update .pyqual/deps.json
- Update .pyqual/llx_history.jsonl
- Update .pyqual/pipeline.db
- Update examples/.gitignore
- Update examples/tests/test_examples.py
- Update project.sh
- ... and 29 more files

## [0.1.30] - 2026-03-27

### Docs
- Update TODO.md
- Update docs/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml

## [0.1.29] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 5 more files

## [0.1.28] - 2026-03-27

### Docs
- Update docs/README.md

### Other
- Update project/duplication.toon.yaml
- Update project/index.html
- Update project/project.toon.yaml

## [0.1.27] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update benchmark_ram_optimization.py
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- ... and 5 more files

## [0.1.26] - 2026-03-27

### Docs
- Update TODO.md

## [0.1.25] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/RAM_OPTIMIZATION.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update test_large_files.py
- Update test_ram_implementation.py

### Other
- Update benchmark_ram_optimization.py
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- ... and 5 more files

## [0.1.24] - 2026-03-27

## [0.1.23] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- Update project/prompt.txt

## [0.1.22] - 2026-03-27

### Docs
- Update TODO.md
- Update docs/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml

## [0.1.21] - 2026-03-27

### Docs
- Update TODO.md
- Update docs/README.md

### Other
- Update project/duplication.toon.yaml

## [0.1.20] - 2026-03-27

### Docs
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml

## [0.1.19] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/context.md

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 3 more files

## [0.1.18] - 2026-03-27

### Other
- Update prefact.yaml

## [0.1.17] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update TODO.md

### Other
- Update planfile.yaml

## [0.1.16] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/context.md

### Other
- Update planfile.yaml
- Update prefact.yaml
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 4 more files

## [0.1.15] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 3 more files

## [0.1.14] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml

## [0.1.13] - 2026-03-27

### Docs
- Update README.md
- Update docs/README.md
- Update project/context.md

### Other
- Update img.png
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- ... and 1 more files

## [0.1.12] - 2026-03-27

## [0.1.11] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/context.md

### Other
- Update PKG-INFO
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- ... and 2 more files

## [0.1.10] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- ... and 1 more files

## [0.1.9] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update prefact.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 7 more files

## [0.1.8] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- ... and 4 more files

## [0.1.7] - 2026-03-27

### Docs
- Update project/context.md

### Other
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/flow.mmd
- Update project/map.toon.yaml

## [0.1.6] - 2026-03-27

### Other
- Update examples/run_examples.py
- Update planfile.yaml
- Update prefact.yaml

## [0.1.5] - 2026-03-27

### Docs
- Update examples/README.md
- Update vscode-extension/node_modules/@eslint-community/eslint-utils/README.md
- Update vscode-extension/node_modules/@eslint-community/regexpp/README.md
- Update vscode-extension/node_modules/@eslint/eslintrc/README.md
- Update vscode-extension/node_modules/@eslint/eslintrc/node_modules/brace-expansion/README.md
- Update vscode-extension/node_modules/@eslint/eslintrc/node_modules/minimatch/README.md
- Update vscode-extension/node_modules/@eslint/js/README.md
- Update vscode-extension/node_modules/@humanwhocodes/config-array/README.md
- Update vscode-extension/node_modules/@humanwhocodes/config-array/node_modules/brace-expansion/README.md
- Update vscode-extension/node_modules/@humanwhocodes/config-array/node_modules/minimatch/README.md
- ... and 297 more files

### Other
- Update examples/07-enterprise/prefact.yaml
- Update examples/08-llm-focused/prefact.yaml
- Update examples/09-high-performance/prefact.yaml
- Update examples/10-plugin-development/prefact.yaml
- Update examples/11-ci-cd/prefact.yaml
- Update examples/12-complete-example/prefact.yaml
- Update examples/requirements.txt
- Update src/prefact/VERSION
- Update vscode-extension/node_modules/.bin/acorn
- Update vscode-extension/node_modules/.bin/eslint
- ... and 965 more files

## [0.1.4] - 2026-03-27

### Docs
- Update README.md
- Update docs/MIGRATION_GUIDE.md
- Update examples/01-individual-rules/README.md
- Update examples/06-api-usage/README.md
- Update examples/README.md
- Update examples/sample-project/README.md

### Test
- Update tests/test_integrations.py

### Other
- Update examples/requirements.txt

## [0.1.3] - 2026-03-27

### Docs
- Update examples/01-individual-rules/duplicate-imports/README.md
- Update examples/01-individual-rules/missing-return-type/README.md
- Update examples/01-individual-rules/print-statements/README.md
- Update examples/01-individual-rules/relative-imports/README.md
- Update examples/01-individual-rules/sorted-imports/README.md
- Update examples/01-individual-rules/string-concat/README.md
- Update examples/01-individual-rules/wildcard-imports/README.md

### Other
- Update examples/03-output-formats/test-report.json
- Update examples/run_all.sh

## [0.1.2] - 2026-03-27

### Docs
- Update README.md
- Update examples/01-individual-rules/README.md
- Update examples/02-multiple-rules/README.md
- Update examples/03-output-formats/README.md
- Update examples/04-custom-rules/README.md
- Update examples/05-ci-cd/README.md
- Update examples/06-api-usage/README.md
- Update examples/README.md
- Update examples/sample-project/README.md

### Other
- Update examples/01-individual-rules/duplicate-imports/after.py
- Update examples/01-individual-rules/duplicate-imports/before.py
- Update examples/01-individual-rules/duplicate-imports/prefact.yaml
- Update examples/01-individual-rules/missing-return-type/after.py
- Update examples/01-individual-rules/missing-return-type/before.py
- Update examples/01-individual-rules/missing-return-type/prefact.yaml
- Update examples/01-individual-rules/print-statements/after.py
- Update examples/01-individual-rules/print-statements/before.py
- Update examples/01-individual-rules/print-statements/prefact.yaml
- Update examples/01-individual-rules/relative-imports/after.py
- ... and 39 more files

## [0.1.1] - 2026-03-27

### Docs
- Update README.md

### Test
- Update tests/test_config.py
- Update tests/test_engine.py
- Update tests/test_relative_imports.py
- Update tests/test_rules.py
- Update tests/test_unused_imports.py

### Other
- Update PKG-INFO
- Update VERSION
- Update prefact/__init__.py
- Update prefact/cli.py
- Update prefact/core.py
- Update prefact/utils.py

## [0.0.6] - 2026-03-27

### Docs
- Update README.md

### Test
- Update tests/test_prefactoring.py

### Other
- Update MANIFEST.in
- Update prefact/__init__.py
- Update prefact/cli.py
- Update prefact/core.py
- Update prefact/utils.py

## [0.0.5] - 2026-03-27

### Other
- Update .idea/inspectionProfiles/Project_Default.xml
- Update .idea/inspectionProfiles/profiles_settings.xml
- Update .idea/misc.xml
- Update .idea/modules.xml
- Update .idea/prefactoring.iml
- Update .idea/vcs.xml

## [0.0.4] - 2026-03-27

## [0.0.3] - 2026-03-27

### Other
- Update MANIFEST.in

## [0.0.2] - 2026-03-27

### Test
- Update tests/test_prefactoring.py

### Other
- Update prefactoring/__init__.py
- Update prefactoring/cli.py
- Update prefactoring/core.py
- Update prefactoring/utils.py

## [0.0.1] - 2026-03-27

### Other
- Update .idea/.gitignore

