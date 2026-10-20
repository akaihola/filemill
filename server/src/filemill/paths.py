"""Path resolution and the symlink mount map.

Every filesystem path that arrives in a URL goes through ``resolve_safe`` before
anything is read. The functions here take the root explicitly: the app owns the
configured ``ROOT`` and passes it in, which keeps this module free of state and
lets tests resolve against any directory.

A public instance (ADR 0087) also refuses hidden paths: ``hidden`` checks the
path a request names, and ``public=True`` makes ``resolve_safe`` check the path
it resolves to.
"""

import os
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import unquote as urlunquote


def symlink_zones(root: Path) -> dict[str, Path]:
    """Return the root and direct symlink targets by mount name."""
    return {
        root.name: root.resolve(),
        **{
            child.name: child.resolve()
            for child in root.iterdir()
            if child.is_symlink()
        },
    }


def dotted(names: Iterable[str]) -> bool:
    """True when one of *names* starts with a dot, as a hidden name does."""
    return any(name.startswith(".") for name in names)


def hidden(rel: str) -> bool:
    """True when a component of the slash-separated request path *rel* is hidden.

    *rel* is stripped and unquoted first, as ``api.rel_to_abs`` and
    ``resolve_safe`` treat it, so `` .git`` and ``%2egit`` are as hidden as
    ``.git``. ``.`` and ``..`` count too.
    """
    return dotted(urlunquote(rel.strip()).split("/"))


def public_zones(root: Path, zones: dict[str, Path]) -> dict[str, Path]:
    """The zones a public instance serves.

    The root, whose path is the operator's choice and is not checked; a direct
    symlink child only when neither its name nor any component of its target
    path is hidden. A child named like the root, which ``symlink_zones`` lets
    replace the root's zone, gets no exemption.
    """
    return {
        name: target
        for name, target in zones.items()
        if (name == root.name and target == root.resolve())
        or not dotted((name, *target.parts))
    }


def visible(path: Path, zones: dict[str, Path]) -> bool:
    """True when the resolved *path* lies in a zone under no hidden name there.

    ``public_zones`` has already dropped bookmarks into hidden folders, so a
    zone can disagree only about a root below a bookmark's hidden folder; the
    root's own files stay visible then.
    """
    return any(
        not dotted(path.relative_to(target).parts)
        for target in zones.values()
        if path.is_relative_to(target)
    )


def resolve_safe(
    path_str: str,
    root: Path,
    zones: dict[str, Path] | None = None,
    *,
    public: bool = False,
) -> Path | None:
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

    With *public*, only ``public_zones`` count, and the resolved path must be
    ``visible``: a symlink into a hidden folder is refused like one that leaves
    the root.
    """
    try:
        zones = zones or symlink_zones(root)
        resolved_root = zones[root.name]
        resolved = Path(os.path.normpath(urlunquote(path_str))).resolve()
        if public:
            return resolved if visible(resolved, public_zones(root, zones)) else None

        # Zone 1: within root
        try:
            resolved.relative_to(resolved_root)
            return resolved
        except ValueError:
            pass

        # Zone 2: within the resolved target of a direct symlink child of root
        for target in zones.values():
            try:
                resolved.relative_to(target)
                return resolved
            except ValueError:
                continue

        return None
    except Exception:
        return None


def mount_targets(root: Path, zones: dict[str, Path] | None = None) -> dict[str, Path]:
    """Return named mounts exposed under ``/w/<mount>/...``.

    The root directory itself is always mounted under ``root.name``. Each direct
    symlink child of *root* is also mounted under the symlink name.
    """
    return zones or symlink_zones(root)


def resolve_web_mount(
    path: str,
    root: Path,
    zones: dict[str, Path] | None = None,
    *,
    public: bool = False,
) -> Path | None:
    """Resolve a ``/w/`` path using named mounts.

    The first path segment names either the root mount (``root.name``) or one of
    root's direct symlink children. The remainder is resolved relative to that
    mount target and still validated through ``resolve_safe()``. With *public*,
    a hidden mount or remainder resolves to None.
    """
    stripped = path.lstrip("/")
    if not stripped:
        return None

    mount_name, _, remainder = stripped.partition("/")
    if public and hidden(remainder):
        return None
    zones = zones or symlink_zones(root)
    mounts = public_zones(root, zones) if public else mount_targets(root, zones)
    target_root = mounts.get(mount_name)
    if target_root is None:
        return None

    candidate = target_root / remainder if remainder else target_root
    return resolve_safe(str(candidate), root, zones, public=public)
