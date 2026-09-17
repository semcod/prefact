"""Append-only event stores backing the Event Sourcing side of CQRS.

An event store is the single source of truth: it only ever appends events and
can replay them in order. Two implementations are provided:

* :class:`InMemoryEventStore` — a plain list, useful for short-lived runs and
  tests.
* :class:`JsonlEventStore` — an append-only JSON-lines file, durable across
  runs and cheap to inspect.
"""

from __future__ import annotations

import abc
import json
from pathlib import Path

from prefact.cqrs.events import from_dict
from prefact.cqrs.events.base import DomainEvent


class EventStore(abc.ABC):
    """Interface every event store must implement."""

    @abc.abstractmethod
    def append(self, event: DomainEvent) -> None:
        """Persist a single event."""

    @abc.abstractmethod
    def load(self) -> list[DomainEvent]:
        """Replay all persisted events in append order."""


class InMemoryEventStore(EventStore):
    """An append-only store kept in memory."""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        self._events.append(event)

    def load(self) -> list[DomainEvent]:
        return list(self._events)

    def __len__(self) -> int:
        return len(self._events)


class JsonlEventStore(EventStore):
    """An append-only store persisted as a JSON-lines file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, event: DomainEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict()) + "\n")

    def load(self) -> list[DomainEvent]:
        if not self.path.exists():
            return []
        events: list[DomainEvent] = []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                events.append(from_dict(json.loads(line)))
        return events
