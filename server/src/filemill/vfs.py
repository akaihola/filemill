"""Virtual filesystem abstraction for filemill.

Defines VFSEntry, VFSProvider (Protocol), VFSRegistry, and the module-level
REGISTRY singleton. Provider modules are imported at the bottom of this file
so their self-registration side-effects run on first import.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

MAX_LABEL_LEN = 60


def _truncate(s: str, n: int = MAX_LABEL_LEN) -> str:
    """Return s truncated to n chars with a trailing ellipsis if longer."""
    return s if len(s) <= n else s[: n - 1] + "…"


@dataclass
class VFSEntry:
    """One navigable item inside a virtual filesystem node."""

    name: str  # display label, already truncated to MAX_LABEL_LEN chars
    vpath: str  # full virtual path key, e.g. "users" or "users/42"
    is_folder: bool  # True → opens a new column on click; False → updates preview
    icon: str  # emoji
    ordered: bool = False  # provider order must be preserved by the UI


@runtime_checkable
class VFSProvider(Protocol):
    """Protocol that concrete VFS providers must implement."""

    def handles(self, path: Path) -> bool: ...

    def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]: ...

    def render_preview(
        self,
        path: Path,
        vpath: str,
        fmt: str,
        page: int,
        limit: int,
        col: int = 0,
    ) -> str: ...

    def default_fmt(self, vpath: str) -> str: ...


class VFSRegistry:
    """Registry mapping file paths to VFSProvider instances."""

    def __init__(self) -> None:
        self._providers: list[VFSProvider] = []

    def register(self, provider: VFSProvider) -> None:
        self._providers.append(provider)

    def get(self, path: Path) -> VFSProvider | None:
        """Return the last-registered provider that handles path, or None."""
        for p in reversed(self._providers):
            if p.handles(path):
                return p
        return None


REGISTRY = VFSRegistry()


def is_vfs_file(path: Path) -> bool:
    """True when path has a registered VFS provider."""
    return REGISTRY.get(path) is not None


# ── Provider registration (side-effects) ──────────────────────────────────────
# These imports MUST remain at the bottom, after all names above are defined.
# Each provider module does `REGISTRY.register(...)` at import time.
from filemill.providers import (
    csv_provider,  # noqa: F401
    json_provider,  # noqa: F401
    sqlite,  # noqa: F401
)
