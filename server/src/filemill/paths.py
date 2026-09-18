"""Path resolution and the symlink mount map.

Every filesystem path that arrives in a URL goes through ``resolve_safe`` before
anything is read. The functions here take the root explicitly: the app owns the
configured ``ROOT`` and passes it in, which keeps this module free of state and
lets tests resolve against any directory.
"""

import os
from pathlib import Path
from urllib.parse import unquote as urlunquote


def resolve_safe(path_str: str, root: Path) -> Path | None:
    """Resolve a user-supplied path and verify it falls within an allowed zone.

    Allowed zones
    -------------
    1. *root* itself – any real file or directory that lives under root.
    2. The resolved target of any *direct* symlink child of root – lets
       directory symlinks placed in root act as bookmarks whose subtrees are
       fully browsable.

    Symlinks *within* a bookmark subtree are only allowed when their resolved
    target falls inside zone 1 or the same zone-2 directory (or another
    bookmark target).  Symlinks that escape all allowed zones are denied.

    Path-traversal via ``..`` is defeated because the containment check
    operates on the fully-resolved path, not the raw string.
    """
    try:
        resolved_root = root.resolve()
        resolved = Path(os.path.normpath(urlunquote(path_str))).resolve()

        # Zone 1: within root
        try:
            resolved.relative_to(resolved_root)
            return resolved
        except ValueError:
            pass

        # Zone 2: within the resolved target of a direct symlink child of root
        for child in root.iterdir():
            if child.is_symlink():
                target = child.resolve()
                try:
                    resolved.relative_to(target)
                    return resolved
                except ValueError:
                    continue

        return None
    except Exception:
        return None


def mount_targets(root: Path) -> dict[str, Path]:
    """Return named mounts exposed under ``/w/<mount>/...``.

    The root directory itself is always mounted under ``root.name``. Each direct
    symlink child of *root* is also mounted under the symlink name.
    """
    mounts = {root.name: root.resolve()}
    for child in root.iterdir():
        if child.is_symlink():
            mounts[child.name] = child.resolve()
    return mounts


def resolve_web_mount(path: str, root: Path) -> Path | None:
    """Resolve a ``/w/`` path using named mounts.

    The first path segment names either the root mount (``root.name``) or one of
    root's direct symlink children. The remainder is resolved relative to that
    mount target and still validated through ``resolve_safe()``.
    """
    stripped = path.lstrip("/")
    if not stripped:
        return None

    mount_name, _, remainder = stripped.partition("/")
    target_root = mount_targets(root).get(mount_name)
    if target_root is None:
        return None

    candidate = target_root / remainder if remainder else target_root
    return resolve_safe(str(candidate), root)
