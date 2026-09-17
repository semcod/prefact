"""Command primitives for the CQRS write side."""

from __future__ import annotations


class Command:
    """Marker base class for command objects.

    A command expresses an intent to change state; it is a plain value object
    carrying the inputs its handler needs. Commands never perform work
    themselves — that is the handler's job.
    """
