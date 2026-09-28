"""Backward-compatible alias for the extended configuration model.

The canonical :class:`ExtendedConfig` lives in :mod:`prefact.config_extended.config`;
it is re-exported here so existing ``config_extended.models`` imports keep working.
"""

from .config import ExtendedConfig

__all__ = ["ExtendedConfig"]
