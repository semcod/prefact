"""In-memory synchronous event bus.

The bus routes a published :class:`~prefact.cqrs.events.base.DomainEvent` to
every handler subscribed to that event's ``name``. When a
:class:`~prefact.cqrs.store.EventStore` is attached, each published event is
appended to it first, making the bus the single integration point for both
projections and event-sourcing persistence.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from prefact.cqrs.events.base import DomainEvent
from prefact.cqrs.store import EventStore

EventHandler = Callable[[DomainEvent], None]


class EventBus:
    """Synchronous pub/sub dispatcher with optional event-store persistence."""

    def __init__(self, store: EventStore | None = None) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self.store = store

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register *handler* to be called for events named *event_name*."""
        self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Remove a previously registered handler."""
        handlers = self._handlers.get(event_name)
        if handlers and handler in handlers:
            handlers.remove(handler)

    def publish(self, event: DomainEvent) -> None:
        """Persist (if a store is attached) and dispatch *event*."""
        if self.store is not None:
            self.store.append(event)
        for handler in list(self._handlers.get(event.name, [])):
            handler(event)

    def handler_count(self, event_name: str | None = None) -> int:
        """Return the number of subscribed handlers (optionally per event)."""
        if event_name is not None:
            return len(self._handlers.get(event_name, []))
        return sum(len(handlers) for handlers in self._handlers.values())
