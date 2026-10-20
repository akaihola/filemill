"""Archive provider: a tarball or a zip is a folder of its members.

Navigation levels follow the member paths: ``docs/readme.md`` is the row
``readme.md`` in the column ``docs``. Directories a tar never recorded are
implied by the members below them, the way a zip's are. Bytes are read from
the archive on demand and never extracted to disk; the member's bytes are
bounded by MEMBER_MAX, the index by MAX_MEMBERS.
"""

from __future__ import annotations

import sys
import tarfile
import zipfile
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from typing import IO, TYPE_CHECKING, cast

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

MEMBER_MAX = 16 * 1024 * 1024  # largest member read into memory for a preview
MAX_MEMBERS = 50_000  # the index stops here; later members are not browsable

TAR_SUFFIXES = (
    ".tar",
    ".tar.gz",
    ".tgz",
    ".tar.bz2",
    ".tbz2",
    ".tar.xz",
    ".txz",
    ".tar.zst",
    ".tzst",
)
ZSTD_SUFFIXES = (".tar.zst", ".tzst")

# Zstandard: the standard library from Python 3.14 (PEP 784), the `zstandard`
# package before that. pyproject.toml requires the package on older interpreters.
if sys.version_info >= (3, 14):
    from compression import zstd as _zstd
else:
    _zstd = None

# Type checking also needs the compatibility API on Python 3.14.
if sys.version_info < (3, 14) or TYPE_CHECKING:
    import zstandard


def zstd_compress(data: bytes) -> bytes:
    """Compress bytes with zstd; tests build fixtures with it."""
    if _zstd is not None:
        return _zstd.compress(data)
    return zstandard.ZstdCompressor().compress(data)


def _zstd_reader(fh: IO[bytes]) -> IO[bytes]:
    if _zstd is not None:
        return cast(IO[bytes], _zstd.ZstdFile(fh))
    return cast(IO[bytes], zstandard.ZstdDecompressor().stream_reader(fh))


def _kind(path: Path) -> str | None:
    """'zip', 'tar' or 'zst' for a name this provider reads, else None."""
    name = path.name.lower()
    if name.endswith(".zip") and len(name) > len(".zip"):
        return "zip"
    for suffix in TAR_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            return "zst" if suffix in ZSTD_SUFFIXES else "tar"
    return None


def _open_tar(path: Path, kind: str) -> tuple[IO[bytes] | None, tarfile.TarFile]:
    if kind == "zst":
        fh: IO[bytes] = path.open("rb")
        try:
            return fh, tarfile.open(fileobj=_zstd_reader(fh), mode="r|")
        except Exception:
            fh.close()
            raise
    return None, tarfile.open(path, "r:*")


def _tar_members(path: Path, kind: str) -> Iterator[tuple[str, tarfile.TarInfo]]:
    """(clean name, member) for every regular file and directory, in order."""
    fh, tf = _open_tar(path, kind)
    try:
        with tf:
            for member in tf:
                if not (member.isfile() or member.isdir()):
                    continue
                clean = clean_member_path(member.name)
                if clean is not None:
                    yield clean, member
    finally:
        if fh is not None:
            fh.close()


# clean name -> (name in the archive, size or None for a directory)
Index = dict[str, tuple[str, int | None]]


@lru_cache(maxsize=32)
def _index(path: str, mtime_ns: int, size: int) -> Index:
    """The archive's members, keyed by virtual path; stat facts key the cache."""
    kind = _kind(Path(path))
    index: Index = {}
    try:
        if kind == "zip":
            with zipfile.ZipFile(path) as zf:
                for info in zf.infolist():
                    clean = clean_member_path(info.filename)
                    if clean is None:
                        continue
                    index[clean] = (
                        info.filename,
                        None if info.is_dir() else info.file_size,
                    )
                    if len(index) >= MAX_MEMBERS:
                        break
        elif kind is not None:
            for clean, member in _tar_members(Path(path), kind):
                index[clean] = (member.name, None if member.isdir() else member.size)
                if len(index) >= MAX_MEMBERS:
                    break
    except Exception:
        return {}
    return index


def _index_of(path: Path) -> Index:
    try:
        st = path.stat()
    except OSError:
        return {}
    return _index(str(path), st.st_mtime_ns, st.st_size)


class ArchiveProvider:
    """VFS provider for tar (plain or compressed) and zip archives."""

    def handles(self, path: Path) -> bool:
        return _kind(path) is not None

    def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]:
        prefix = vpath + "/" if vpath else ""
        children: dict[str, bool] = {}
        for name, (_original, size) in _index_of(path).items():
            if not name.startswith(prefix) or name == vpath:
                continue
            rest = name[len(prefix) :]
            head, _, tail = rest.partition("/")
            folder = bool(tail) or size is None
            children[head] = children.get(head, False) or folder
        return [
            VFSEntry(
                name=_truncate(head),
                vpath=prefix + head,
                is_folder=folder,
                icon=FOLDER_ICON if folder else FILE_ICON,
                ordered=True,
            )
            for head, folder in sorted(
                children.items(), key=lambda item: entry_order_key(item[0], item[1])
            )
        ]

    def member(self, path: Path, vpath: str) -> VFSMember | None:
        """A file member's bytes, or None for a folder or an unknown name.

        A member over MEMBER_MAX keeps its name and size but carries no bytes.
        """
        found = _index_of(path).get(vpath) if vpath else None
        if found is None:
            return None
        original, size = found
        if size is None:
            return None
        name = vpath.rsplit("/", 1)[-1]
        if size > MEMBER_MAX:
            return VFSMember(name=name, size=size, data=None)
        try:
            return VFSMember(name=name, size=size, data=self._read(path, original))
        except Exception:
            return None

    def _read(self, path: Path, original: str) -> bytes:
        kind = _kind(path)
        if kind == "zip":
            with zipfile.ZipFile(path) as zf:
                return zf.read(original)
        # A streamed tar member is readable only while the walk is on it.
        fh, tf = _open_tar(path, kind or "tar")
        try:
            with tf:
                for member in tf:
                    if member.name == original and member.isfile():
                        extracted = tf.extractfile(member)
                        return extracted.read() if extracted else b""
        finally:
            if fh is not None:
                fh.close()
        raise KeyError(original)


REGISTRY.register(ArchiveProvider())
