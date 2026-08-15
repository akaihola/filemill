# Milestone 03 – Virtual filesystem protocol

pykofinder doesn't just browse real directories. SQLite databases,
JSON files, and CSV spreadsheets can be navigated as though they were
folder trees – tables become folders, rows become entries, cells become
key-value detail views. This extensibility is powered by a simple
_virtual filesystem_ (VFS) abstraction defined in this milestone.

We define the protocol and the registry here but register no providers yet.
The app routes (Milestone 6) will check the registry on every click; with no
providers registered, VFS code paths remain dormant until we bring them to
life in Milestone 8.

## VFS entry

A `VFSEntry` represents one item inside a virtual tree – a table, a row,
a schema folder. The `vpath` field carries the full virtual path key
(e.g. `"users"` or `"users/42"`) which the server round-trips through
query parameters.

```python src/pykofinder/vfs.py
"""Virtual filesystem abstraction for pykofinder.

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


<<<vfs provider protocol>>>


<<<vfs registry>>>


REGISTRY = VFSRegistry()


def is_vfs_file(path: Path) -> bool:
    """True when path has a registered VFS provider."""
    return REGISTRY.get(path) is not None


<<<vfs provider imports>>>
```

## Provider protocol

Any class that implements four methods – `handles`, `list_entries`,
`render_preview`, and `default_fmt` – can serve as a VFS provider.
We use `typing.Protocol` with `runtime_checkable` so providers don't
need to inherit from a base class; duck-typing suffices.

```python "vfs provider protocol"
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
```

## Registry

The registry is a simple list. Providers self-register via
`REGISTRY.register(...)` at import time. When looking up a path,
we walk the list in reverse so that later registrations take priority –
this lets users override built-in providers.

```python "vfs registry"
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
```

## Provider imports (stub)

At the bottom of `vfs.py` we import provider modules whose top-level code
calls `REGISTRY.register(...)`. For now the import section is empty;
Milestone 8 will replace this stub with the real imports.

```python "vfs provider imports"
# ── Provider registration (side-effects) ──────────────────────────────────────
# Provider imports will be added in Milestone 8.
```

## Providers package

The `providers/` sub-package needs its own `__init__.py`.

```python src/pykofinder/providers/__init__.py
# providers package – each sub-module self-registers via REGISTRY.register(...)
```

## Verification

```bash
rm -rf _tangle_out && mkdir _tangle_out && cd _tangle_out
lmt ../01-*.md ../02-*.md ../03-*.md
uv sync
python -c "
from pykofinder.vfs import REGISTRY, VFSEntry, is_vfs_file
from pathlib import Path
print('Registry providers:', len(REGISTRY._providers))
print('is_vfs_file(Path(\"test.db\")):', is_vfs_file(Path('test.db')))
e = VFSEntry(name='users', vpath='users', is_folder=True, icon='📁')
print('VFSEntry:', e)
"
```

The registry is empty, so `is_vfs_file` returns `False` for everything.
