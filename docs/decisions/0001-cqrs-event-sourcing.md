# ADR-0001: CQRS + Event Sourcing foundation

- **Status:** accepted
- **Date:** 2026-09-17
- **Deciders:** prefact maintainers
- **Context ticket:** PLF-001

## Context

prefact runs a single imperative pipeline (`scan → fix → validate`) that mixes
reads (file discovery, scanning, validation) with writes (applying fixes) in one
place (`prefact/engine.py`). As the tool grows — more rules, plugins, and
eventual replays/audits of what it changed — that coupling makes the code harder
to reason about and prevents reconstructing *what happened* during a run.

## Decision

Introduce a CQRS + Event Sourcing foundation, split along two bounded contexts
that mirror the pipeline's read and write halves:

- **`analysis`** (query side, `prefact/cqrs/queries/`) — discovers files, scans
  sources, and validates fixed output. It has no side effects on the codebase.
- **`refactoring`** (command side, `prefact/cqrs/commands/`) — applies fixes to
  files. It is the only place that writes.

Supporting pieces:

- `prefact/cqrs/events/` — immutable domain events (`analysis.*` and
  `refactoring.*`), registered for (de)serialisation.
- `prefact/cqrs/bus.py` — synchronous in-memory `EventBus`; publishes to
  subscribers and, when attached, to an event store.
- `prefact/cqrs/store.py` — append-only `EventStore` with an in-memory and a
  JSON-lines implementation, so runs can be replayed.

The existing `Scanner`, `Fixer`, and `Validator` become the adapters invoked by
the new query/command handlers. `RefactoringEngine` keeps the imperative
orchestration (RAM preloading, large-file splitting) and delegates each step to
a handler, publishing events as it goes. `Config.event_store` selects a durable
JSON-lines store; otherwise an in-memory store is used.

## Consequences

- Behaviour of `scan`/`fix`/`validate` is unchanged; all existing tests pass.
- Every pipeline step is now observable via `engine.bus` and replayable via
  `engine.store`.
- The split is the *first step*: later work can move each handler to its own
  bounded-context module, add projections, and replay events to rebuild state.
