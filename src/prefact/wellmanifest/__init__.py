"""Wellmanifest standards integration for prefact.

Provides governance guard against mutating primary checkouts on main,
and worktree allocation / merge disposition helpers conforming to:
- wellmanifest/new-project
- wellmanifest/worktrees
- wellmanifest/merge
"""

from prefact.wellmanifest.guard import (
    WellmanifestViolationError,
    find_wellmanifest_root,
    is_safe_to_modify,
    is_wellmanifest_repo,
)
from prefact.wellmanifest.worktree import (
    TicketAllocation,
    WellmanifestWorktreeManager,
)

__all__ = [
    "WellmanifestViolationError",
    "find_wellmanifest_root",
    "is_safe_to_modify",
    "is_wellmanifest_repo",
    "TicketAllocation",
    "WellmanifestWorktreeManager",
]
