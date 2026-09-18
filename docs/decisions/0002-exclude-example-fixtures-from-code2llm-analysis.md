# ADR-0002: Exclude example fixtures from code2llm analysis

- **Status:** accepted
- **Date:** 2026-09-18
- **Deciders:** prefact maintainers
- **Context ticket:** PLF-028

## Context

code2llm's duplication detector flagged the `DataProcessor` classes in
`examples/01-individual-rules/unused-imports/before.py` and `after.py`
(3 overlapping methods) and auto-created ticket PLF-028
(`code2llm:dup:DataProcessor:...before.py:...after.py`) proposing a shared
base class or merge.

The flagged files are a before/after fixture pair for the `unused-imports`
rule demo. `after.py` must remain exactly what `prefact fix` produces from
`before.py`, so the pair — like every rule directory under
`examples/01-individual-rules/` (see `examples/generate_examples.py` and
`examples/01-individual-rules/README.md`) — is near-identical **by design**.
Extracting a shared base between the two would break the standalone demo
(each directory is scanned on its own via its local `prefact.yaml`) and
would be inconsistent with the other seven rule fixtures, which trigger the
same class of finding (`process_data`, `add`, `get_user`, `process`, …).

This is a known false-positive category for the ticket generator
(`code2llm/exporters/planfile_tickets.py` flags any same-named class pair
with ≥60% method-name overlap, with no fixture awareness). The koru
repository hit the identical problem with intentionally duplicated
per-IDE plugin classes (STARTER-276) and resolved it by excluding the
duplicated tree from analysis (`koru/autonomy/code2llm_discovery.py`
`DEFAULT_EXCLUDES`), not by consolidating the code.

## Decision

1. Do **not** consolidate the fixture pair; `before.py`/`after.py` stay
   standalone and self-contained.
2. Exclude the `examples/` tree from code2llm analysis for this repository
   by overriding the `code2llm` tool preset in `pyqual.tools.json`
   (`--exclude examples` on the pyqual `analyze` stage invocation
   `code2llm {workdir} -f all -o ./project --no-chunk`).
3. Follow-up (out of repo, semcod/koru): koru's own idle-discovery runs use
   hardcoded `DEFAULT_EXCLUDES = ("*.md", "plugins")`; adding `examples`
   there needs its own koru ticket, mirroring the `plugins` precedent.

## Consequences

- Duplicate-class and code-smell tickets no longer originate from demo
  fixtures; ~18 of 257 ticket suggestions in the 2026-09-18 baseline
  referenced `examples/` and were fixture noise.
- Real duplication inside `examples/` (e.g. a broken fixture) is no longer
  reported by code2llm; accepted, since fixtures are reviewed as demo
  content, and `prefact scan` on each example directory still validates
  their rule behavior.
- Verification (PLF-028): re-running
  `code2llm <repo> -f planfile --no-chunk --exclude examples` produces no
  `code2llm:dup:DataProcessor` ticket and no `examples/`-referencing
  dedupe keys; baseline without the exclude reproduces the ticket.
