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
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
RICH_EXTENSIONS = {".md", ".markdown", ".rst", ".docx", ".pptx"}


def entry_order_key(name: str, is_folder: bool) -> tuple[bool, str, str]:
    """Directories first, then case-insensitive name order."""
    return (not is_folder, name.casefold(), name)


@dataclass(frozen=True)
class FileKind:
    kind: str
    preview: str
    editable: bool


def classify_path(
    path: Path, *, is_dir: bool = False, virtual: bool = False, provider: bool = False
) -> FileKind:
    """Return the shared filesystem, preview, and edit classification."""
    if is_dir:
        return FileKind("folder", "none", False)
    if virtual:
        return FileKind("vfs", "virtual", False)
    if provider:
        return FileKind("vfs", "virtual", False)
    ext = path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return FileKind("file", "image", False)
    if ext == ".pdf":
        return FileKind("file", "pdf", False)
    if ext in {".html", ".htm"}:
        return FileKind("file", "html", False)
    if ext == ".desktop":
        return FileKind("link", "desktop", False)
    if ext == ".vtt":
        return FileKind("file", "vtt", True)
    if ext in {".jsonl", ".csv"}:
        return FileKind("file", ext[1:], True)
    if ext in RICH_EXTENSIONS:
        return FileKind("file", ext[1:], ext in {".md", ".markdown", ".rst"})
    return FileKind("file", "text", True)


def clean_member_path(name: str) -> str | None:
    """A member name as a virtual path, or None when it cannot be one.

    Leading slashes and ``.`` segments go; a ``..`` anywhere drops the member.
    Nothing is written to disk, so this is about one address per member, not
    about containment.
    """
    parts = [p for p in name.replace("\\", "/").split("/") if p and p != "."]
    if not parts or ".." in parts:
        return None
    return "/".join(parts)


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
    record: dict[str, object] | None = None  # a row's cells; the client draws them


@runtime_checkable
class VFSProvider(Protocol):
    """Protocol that concrete VFS providers must implement."""

    def handles(self, path: Path) -> bool: ...

    def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]: ...


@dataclass(frozen=True)
class VFSMember:
    """A leaf inside a virtual filesystem that has bytes of its own."""

    name: str  # the member's own file name, which says how to preview it
    size: int
    data: bytes | None  # None when the member is over the provider's limit


@runtime_checkable
class VFSMemberProvider(Protocol):
    """A provider whose leaves are files: archives, not database rows."""

    def member(self, path: Path, vpath: str) -> VFSMember | None: ...


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


# ── Provider registration (side-effects) ──────────────────────────────────────
# These imports MUST remain at the bottom, after all names above are defined.
# Each provider module does `REGISTRY.register(...)` at import time.
from filemill.providers import archive, gitbundle, sqlite, vtt_provider

# Registration is complete; the registry owns the provider instances.
del archive, gitbundle, sqlite, vtt_provider
