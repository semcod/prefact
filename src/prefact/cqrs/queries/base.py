"""Query primitives for the CQRS read side."""

from __future__ import annotations


class Query:
    """Marker base class for query objects.

    A query is a request for information. It is a plain value object and has no
    side effects; its handler performs the read and returns the result.
    """
