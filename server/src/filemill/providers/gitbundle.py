"""Git bundle provider: a ``.bundle`` is a folder of its refs, each a tree.

The first columns follow the ref names with ``refs/`` dropped: ``heads`` →
``main``, ``tags`` → ``v1``, and ``HEAD`` when the bundle carries it. Those
come from the bundle's text header, read here without ``git``. Below a ref the
columns are the commit's tree, one level per column, and a blob is a file
member; for those ``git`` unbundles the file once into a temporary bare
repository retained by its cache entry and active reads; nothing else is written.
A bundle over BUNDLE_MAX, a bundle with prerequisites (an incremental one,
whose objects are elsewhere), a broken bundle and a bundle on a host without
``git`` are plain files. A blob over MEMBER_MAX is listed but not read.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from filemill.vfs import (
    REGISTRY,
    VFSEntry,
    VFSMember,
    _truncate,
    clean_member_path,
    entry_order_key,
)

FOLDER_ICON = "📁"
FILE_ICON = "📄"
REF_ICON = "🔖"

MEMBER_MAX = 16 * 1024 * 1024  # largest blob read into memory for a preview
BUNDLE_MAX = 512 * 1024 * 1024  # a larger bundle is a plain file
HEADER_MAX = 1024 * 1024  # a header longer than this is not one
GIT_TIMEOUT = 60  # seconds per git call

GIT = shutil.which("git")

Refs = dict[str, str]  # short ref name (refs/ dropped) -> sha


@lru_cache(maxsize=64)
def _refs(path: str, mtime_ns: int, size: int) -> Refs:
    """The refs named in the bundle header; empty when it is not a usable one.

    The header is text: a signature line, capability lines on v3, ``-<sha>``
    prerequisite lines, ``<sha> <ref>`` lines, then an empty line and the
    pack. A prerequisite means the objects are elsewhere, so nothing lists.
    """
    try:
        with open(path, "rb") as fh:
            head = fh.read(HEADER_MAX)
    except OSError:
        return {}
    signature, _, rest = head.partition(b"\n")
    if signature not in (b"# v2 git bundle", b"# v3 git bundle"):
        return {}
    header, sep, _pack = rest.partition(b"\n\n")
    if not sep:
        return {}
    refs: Refs = {}
    for line in header.decode("utf-8", "replace").splitlines():
        if line.startswith("-"):
            return {}
        if line.startswith("@"):
            continue
        sha, _, name = line.partition(" ")
        if name and all(c in "0123456789abcdef" for c in sha) and len(sha) >= 40:
            refs[name.removeprefix("refs/")] = sha
    return refs


def _git(repo: Path, *args: str, input: bytes | None = None) -> bytes:
    """Stdout of ``git -C repo args``; failures reach the provider error path.

    The environment hides the user's git configuration and never prompts.
    """
    if GIT is None:
        raise RuntimeError("Git is not available")
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(repo),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
    }
    done = subprocess.run(
        [GIT, "-C", str(repo), *args],
        capture_output=True,
        input=input,
        env=env,
        timeout=GIT_TIMEOUT,
        check=False,
    )
    if done.returncode:
        raise RuntimeError(
            f"Git {args[0]} failed: {done.stderr.decode('utf-8', 'replace').strip()}"
        )
    return done.stdout


@lru_cache(maxsize=8)
def _repo(path: str, mtime_ns: int, size: int) -> tempfile.TemporaryDirectory[str]:
    """Unbundle *path* once into a temporary bare repository; stat facts key
    the cache. Active reads also retain the owner until their last Git call."""
    tmp = tempfile.TemporaryDirectory(prefix="filemill-bundle-")
    repo = Path(tmp.name)
    try:
        _git(repo, "init", "-q", "--bare")
        _git(repo, "bundle", "unbundle", path)
    except Exception:
        tmp.cleanup()
        raise
    return tmp


@dataclass(frozen=True)
class _Bundle:
    path: Path
    refs: Refs
    mtime_ns: int
    size: int

    @property
    def repo(self) -> tempfile.TemporaryDirectory[str]:
        return _repo(str(self.path), self.mtime_ns, self.size)


def _bundle_of(path: Path) -> _Bundle | None:
    try:
        st = path.stat()
    except OSError:
        return None
    if st.st_size > BUNDLE_MAX:
        return None
    refs = _refs(str(path), st.st_mtime_ns, st.st_size)
    return _Bundle(path, refs, st.st_mtime_ns, st.st_size) if refs else None


def _split(bundle: _Bundle, vpath: str) -> tuple[str, str] | None:
    """(ref sha, tree path) when *vpath* is at or below a ref, else None."""
    for short, sha in bundle.refs.items():
        if vpath == short:
            return sha, ""
        if vpath.startswith(short + "/"):
            return sha, vpath[len(short) + 1 :]
    return None


def _entry(vpath: str, folder: bool, icon: str) -> VFSEntry:
    return VFSEntry(
        name=_truncate(vpath.rsplit("/", 1)[-1]),
        vpath=vpath,
        is_folder=folder,
        icon=icon,
        ordered=True,
    )


class GitBundleProvider:
    """VFS provider for Git bundles, read through the ``git`` executable."""

    def handles(self, path: Path) -> bool:
        name = path.name.lower()
        return GIT is not None and name.endswith(".bundle") and name != ".bundle"

    def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]:
        bundle = _bundle_of(path)
        if bundle is None:
            return []
        below = _split(bundle, vpath)
        if below is None:
            return self._ref_level(bundle, vpath)
        sha, tree = below
        if tree and clean_member_path(tree) != tree:
            return []
        return self._tree_level(bundle, sha, vpath, tree)

    def _ref_level(self, bundle: _Bundle, vpath: str) -> list[VFSEntry]:
        prefix = vpath + "/" if vpath else ""
        heads = {
            short[len(prefix) :].partition("/")[0]
            for short in bundle.refs
            if short.startswith(prefix)
        }
        return [
            _entry(prefix + head, True, REF_ICON)
            for head in sorted(heads, key=lambda h: entry_order_key(h, True))
        ]

    def _tree_level(
        self, bundle: _Bundle, sha: str, vpath: str, tree: str
    ) -> list[VFSEntry]:
        owner = bundle.repo
        listed = _git(Path(owner.name), "ls-tree", "-z", f"{sha}:{tree}")
        children: list[tuple[str, bool]] = []
        for item in listed.decode("utf-8", "replace").split("\0"):
            facts, _, name = item.partition("\t")
            kind = facts.split(" ")[1] if facts.count(" ") == 2 else ""
            if name and kind in ("blob", "tree"):
                children.append((name, kind == "tree"))
        return [
            _entry(f"{vpath}/{name}", folder, FOLDER_ICON if folder else FILE_ICON)
            for name, folder in sorted(
                children, key=lambda item: entry_order_key(item[0], item[1])
            )
        ]

    def member(self, path: Path, vpath: str) -> VFSMember | None:
        """A blob's bytes, or None for a ref, a tree or an unknown name."""
        bundle = _bundle_of(path) if vpath else None
        below = _split(bundle, vpath) if bundle is not None else None
        if bundle is None or below is None:
            return None
        sha, tree = below
        if not tree or clean_member_path(tree) != tree:
            return None
        owner = bundle.repo
        repo = Path(owner.name)
        facts = _git(
            repo,
            "cat-file",
            "--batch-check=%(objecttype) %(objectsize)",
            "-z",
            input=f"{sha}:{tree}\0".encode(),
        ).split()
        if len(facts) != 2 or facts[0] != b"blob":
            return None
        size = int(facts[1])
        name = tree.rsplit("/", 1)[-1]
        if size > MEMBER_MAX:
            return VFSMember(name=name, size=size, data=None)
        data = _git(repo, "cat-file", "blob", f"{sha}:{tree}")
        return VFSMember(name=name, size=size, data=data)


REGISTRY.register(GitBundleProvider())
