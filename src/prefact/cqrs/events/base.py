"""Base primitives for domain events."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar


def utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _jsonable(value: Any) -> Any:
    """Convert a value into a JSON-serialisable representation."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for every domain event.

    Events are immutable value objects. Concrete subclasses declare a unique
    ``name`` (a ``ClassVar``) used for routing on the bus and for serialising to
    the event store.
    """

    name: ClassVar[str] = ""

    occurred_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the event to a plain dictionary (excluding class metadata)."""
        payload: dict[str, Any] = {"name": self.name}
        for f in fields(self):
            payload[f.name] = _jsonable(getattr(self, f.name))
        return payload
