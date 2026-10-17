"""The archive provider: one level of a tarball or zip per column."""

import io
import os
import tarfile
import zipfile
from pathlib import Path

import pytest

from filemill.providers.archive import MEMBER_MAX, ArchiveProvider, zstd_compress

MEMBERS = {
    "top.txt": b"top level\n",
    "docs/readme.md": b"# Hello\n",
    "docs/pic.png": b"\x89PNG\r\n",
    "src/app.py": b"print('hi')\n",
    "src/pkg/__init__.py": b"",
}


def tar_bytes(members: dict[str, bytes], with_dirs: bool = False) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        if with_dirs:
            info = tarfile.TarInfo("docs")
            info.type = tarfile.DIRTYPE
            tf.addfile(info)
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


@pytest.fixture()
def tar_zst(tmp_path: Path) -> Path:
    path = tmp_path / "demo.tar.zst"
    path.write_bytes(zstd_compress(tar_bytes(MEMBERS)))
    return path


@pytest.fixture()
def zip_file(tmp_path: Path) -> Path:
    path = tmp_path / "demo.zip"
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in MEMBERS.items():
            zf.writestr(name, data)
    return path


def names(entries) -> list[str]:
    return [e.name for e in entries]


def test_handles_tar_zip_and_the_compressed_tar_suffixes(tmp_path: Path):
    p = ArchiveProvider()
    for name in (
        "a.tar",
        "a.tar.gz",
        "a.tgz",
        "a.tar.bz2",
        "a.tbz2",
        "a.tar.xz",
        "a.txz",
        "a.tar.zst",
        "a.tzst",
        "a.zip",
        "A.TAR.ZST",
    ):
        assert p.handles(tmp_path / name), name
    for name in ("a.txt", "a.gz", "a.zst", "a.db", "tar.zst"):
        assert not p.handles(tmp_path / name), name


def test_the_top_level_lists_folders_first_then_files(tar_zst: Path):
    entries = ArchiveProvider().list_entries(tar_zst, "")
    assert names(entries) == ["docs", "src", "top.txt"]
    assert [e.is_folder for e in entries] == [True, True, False]
    assert [e.vpath for e in entries] == ["docs", "src", "top.txt"]
    assert all(e.icon for e in entries)


def test_a_folder_lists_one_level_only(tar_zst: Path):
    entries = ArchiveProvider().list_entries(tar_zst, "src")
    assert names(entries) == ["pkg", "app.py"]
    assert entries[0].vpath == "src/pkg"
    assert entries[1].vpath == "src/app.py"
    assert names(ArchiveProvider().list_entries(tar_zst, "src/pkg")) == ["__init__.py"]


def test_implicit_and_explicit_directories_list_the_same(tmp_path: Path):
    implicit = tmp_path / "implicit.tar"
    implicit.write_bytes(tar_bytes(MEMBERS))
    explicit = tmp_path / "explicit.tar"
    explicit.write_bytes(tar_bytes(MEMBERS, with_dirs=True))
    p = ArchiveProvider()
    assert names(p.list_entries(implicit, "")) == names(p.list_entries(explicit, ""))
    assert names(p.list_entries(implicit, "docs")) == ["pic.png", "readme.md"]


def test_a_zip_lists_like_a_tar(zip_file: Path):
    p = ArchiveProvider()
    assert names(p.list_entries(zip_file, "")) == ["docs", "src", "top.txt"]
    assert names(p.list_entries(zip_file, "docs")) == ["pic.png", "readme.md"]


def test_a_missing_folder_or_a_file_lists_nothing(tar_zst: Path):
    p = ArchiveProvider()
    assert p.list_entries(tar_zst, "nope") == []
    assert p.list_entries(tar_zst, "top.txt") == []


def test_a_member_reads_its_bytes_and_name(tar_zst: Path, zip_file: Path):
    for archive in (tar_zst, zip_file):
        member = ArchiveProvider().member(archive, "docs/readme.md")
        assert member is not None
        assert member.name == "readme.md"
        assert member.data == b"# Hello\n"
        assert member.size == len(b"# Hello\n")


def test_a_folder_or_a_missing_name_is_no_member(tar_zst: Path):
    p = ArchiveProvider()
    assert p.member(tar_zst, "docs") is None
    assert p.member(tar_zst, "nope.txt") is None
    assert p.member(tar_zst, "") is None


def test_an_oversized_member_keeps_its_size_but_not_its_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("filemill.providers.archive.MEMBER_MAX", 4)
    path = tmp_path / "big.tar"
    path.write_bytes(tar_bytes({"big.bin": b"12345", "ok.bin": b"1234"}))
    p = ArchiveProvider()
    big = p.member(path, "big.bin")
    assert big is not None and big.data is None and big.size == 5
    ok = p.member(path, "ok.bin")
    assert ok is not None and ok.data == b"1234"
    assert MEMBER_MAX > 4  # the module constant is what the API reports


def test_escaping_member_names_are_dropped_and_prefixes_normalised(tmp_path: Path):
    path = tmp_path / "hostile.tar"
    path.write_bytes(
        tar_bytes(
            {
                "../evil.txt": b"x",
                "/abs.txt": b"abs",
                "./dot/inner.txt": b"inner",
                "a/../b.txt": b"x",
            }
        )
    )
    p = ArchiveProvider()
    assert names(p.list_entries(path, "")) == ["dot", "abs.txt"]
    assert names(p.list_entries(path, "dot")) == ["inner.txt"]
    member = p.member(path, "dot/inner.txt")
    assert member is not None and member.data == b"inner"
    assert p.member(path, "../evil.txt") is None


def test_a_broken_archive_lists_nothing_and_has_no_members(tmp_path: Path):
    path = tmp_path / "broken.tar.zst"
    path.write_bytes(b"not an archive at all")
    p = ArchiveProvider()
    assert p.list_entries(path, "") == []
    assert p.member(path, "x") is None


def test_a_listing_is_cached_until_the_file_changes(tmp_path: Path):
    path = tmp_path / "demo.tar"
    path.write_bytes(tar_bytes({"one.txt": b"1"}))
    p = ArchiveProvider()
    assert names(p.list_entries(path, "")) == ["one.txt"]
    before = path.stat()
    path.write_bytes(tar_bytes({"two.txt": b"22"}))
    # Tar padding keeps the size unchanged; make the cache-key change explicit
    # even on filesystems where both writes get the same timestamp.
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
    assert names(p.list_entries(path, "")) == ["two.txt"]


def test_the_archive_provider_is_registered(tmp_path: Path):
    from filemill.vfs import REGISTRY

    assert REGISTRY.get(tmp_path / "x.tar.zst") is not None
    assert REGISTRY.get(tmp_path / "x.zip") is not None
