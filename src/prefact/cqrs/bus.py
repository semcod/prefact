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
from typing import NamedTuple

from prefact.cqrs.events.base import DomainEvent
from prefact.cqrs.store import EventStore

EventHandler = Callable[[DomainEvent], None]


class Subscription(NamedTuple):
    """Identity of a handler registered for one event name."""

    event_name: str
    handler: EventHandler


class EventBus:
    """Synchronous pub/sub dispatcher with optional event-store persistence."""

    def __init__(self, store: EventStore | None = None) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self.store = store

    def subscribe(self, subscription: Subscription) -> None:
        """Register the subscription's handler for its event name."""
        self._handlers[subscription.event_name].append(subscription.handler)

    def unsubscribe(self, subscription: Subscription) -> None:
        """Remove a previously registered subscription."""
        handlers = self._handlers.get(subscription.event_name)
        if handlers and subscription.handler in handlers:
            handlers.remove(subscription.handler)

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
