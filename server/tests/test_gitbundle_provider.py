"""The Git bundle provider: refs as folders, then one tree level per column."""

import shutil
import subprocess
from pathlib import Path

import pytest

from filemill.providers.gitbundle import MEMBER_MAX, GitBundleProvider

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")

MEMBERS = {
    "top.txt": b"top level\n",
    "docs/readme.md": b"# Hello\n",
    "docs/pic.png": b"\x89PNG\r\n",
    "src/app.py": b"print('hi')\n",
    "src/pkg/__init__.py": b"",
}


@pytest.fixture()
def bundle(tmp_path: Path, bundle_builder) -> Path:
    return bundle_builder(tmp_path / "demo.bundle", MEMBERS, tags=["v1"])


def names(entries) -> list[str]:
    return [e.name for e in entries]


def test_handles_bundle_files_only(tmp_path: Path):
    p = GitBundleProvider()
    assert p.handles(tmp_path / "a.bundle")
    assert p.handles(tmp_path / "A.BUNDLE")
    for name in ("a.txt", ".bundle", "a.bundle.txt", "a.tar"):
        assert not p.handles(tmp_path / name), name


def test_the_top_level_lists_the_ref_namespaces(bundle: Path):
    entries = GitBundleProvider().list_entries(bundle, "")
    assert names(entries) == ["HEAD", "heads", "tags"]
    assert [e.vpath for e in entries] == ["HEAD", "heads", "tags"]
    assert all(e.is_folder for e in entries)


def test_a_namespace_lists_its_refs(bundle: Path):
    p = GitBundleProvider()
    assert [(e.name, e.vpath) for e in p.list_entries(bundle, "heads")] == [
        ("main", "heads/main")
    ]
    assert [e.vpath for e in p.list_entries(bundle, "tags")] == ["tags/v1"]


def test_a_ref_lists_its_tree_folders_first(bundle: Path):
    for ref in ("HEAD", "heads/main", "tags/v1"):
        entries = GitBundleProvider().list_entries(bundle, ref)
        assert names(entries) == ["docs", "src", "top.txt"], ref
        assert [e.is_folder for e in entries] == [True, True, False]
        assert [e.vpath for e in entries] == [
            f"{ref}/docs",
            f"{ref}/src",
            f"{ref}/top.txt",
        ]


def test_a_tree_lists_one_level_only(bundle: Path):
    p = GitBundleProvider()
    entries = p.list_entries(bundle, "heads/main/src")
    assert names(entries) == ["pkg", "app.py"]
    assert entries[0].vpath == "heads/main/src/pkg"
    assert names(p.list_entries(bundle, "heads/main/src/pkg")) == ["__init__.py"]


def test_unknown_refs_list_nothing_and_invalid_trees_report_errors(bundle: Path):
    p = GitBundleProvider()
    assert p.list_entries(bundle, "nope") == []
    assert p.list_entries(bundle, "heads/nope") == []
    for vpath in ("heads/main/nope", "heads/main/top.txt"):
        with pytest.raises(RuntimeError, match="Git ls-tree failed"):
            p.list_entries(bundle, vpath)
    assert p.list_entries(bundle, "heads/main/../x") == []


def test_a_member_reads_its_bytes_and_name(bundle: Path):
    member = GitBundleProvider().member(bundle, "heads/main/docs/readme.md")
    assert member is not None
    assert member.name == "readme.md"
    assert member.data == b"# Hello\n"
    assert member.size == len(b"# Hello\n")


def test_a_folder_a_ref_or_a_missing_name_is_no_member(bundle: Path):
    p = GitBundleProvider()
    assert p.member(bundle, "heads/main/docs") is None
    assert p.member(bundle, "heads/main") is None
    assert p.member(bundle, "heads") is None
    assert p.member(bundle, "heads/main/nope.txt") is None
    assert p.member(bundle, "heads/main/../top.txt") is None
    assert p.member(bundle, "") is None


def test_an_oversized_member_keeps_its_size_but_not_its_bytes(
    bundle: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("filemill.providers.gitbundle.MEMBER_MAX", 4)
    p = GitBundleProvider()
    big = p.member(bundle, "heads/main/top.txt")
    assert big is not None and big.data is None and big.size == len(b"top level\n")
    assert MEMBER_MAX > 4


def test_a_broken_or_oversized_bundle_lists_nothing(
    tmp_path: Path, bundle: Path, monkeypatch: pytest.MonkeyPatch
):
    p = GitBundleProvider()
    broken = tmp_path / "broken.bundle"
    broken.write_bytes(b"not a bundle at all")
    assert p.list_entries(broken, "") == []
    assert p.member(broken, "HEAD/x") is None
    monkeypatch.setattr("filemill.providers.gitbundle.BUNDLE_MAX", 4)
    assert p.list_entries(bundle, "") == []


def test_listing_refs_reads_the_header_only(bundle: Path, monkeypatch):
    """The root listing asks every bundle whether it is non-empty; that must
    not unbundle it. Only a tree level or a blob needs git."""
    monkeypatch.setattr("filemill.providers.gitbundle._git", lambda *a: None)
    p = GitBundleProvider()
    assert names(p.list_entries(bundle, "")) == ["HEAD", "heads", "tags"]
    assert names(p.list_entries(bundle, "heads")) == ["main"]


def test_an_incremental_bundle_lists_nothing(tmp_path: Path, bundle_builder):
    """A bundle made with prerequisites needs objects it does not carry."""
    repo = tmp_path / "repo"
    bundle_builder(tmp_path / "full.bundle", {"a.txt": b"a\n"}, repo=repo)
    (repo / "b.txt").write_bytes(b"b\n")
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "add", "."], check=True)
    subprocess.run([*git, "commit", "-qm", "more"], check=True)
    inc = tmp_path / "inc.bundle"
    subprocess.run(
        [*git, "bundle", "create", "-q", str(inc), "HEAD~1..HEAD"], check=True
    )
    assert GitBundleProvider().list_entries(inc, "") == []


def test_a_listing_is_cached_until_the_file_changes(tmp_path: Path, bundle_builder):
    path = tmp_path / "demo.bundle"
    bundle_builder(path, {"one.txt": b"1"}, repo=tmp_path / "r1")
    p = GitBundleProvider()
    assert names(p.list_entries(path, "HEAD")) == ["one.txt"]
    bundle_builder(path, {"two.txt": b"2" * 100}, repo=tmp_path / "r2")
    assert names(p.list_entries(path, "HEAD")) == ["two.txt"]


def test_without_git_a_bundle_is_a_plain_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("filemill.providers.gitbundle.GIT", None)
    assert not GitBundleProvider().handles(tmp_path / "a.bundle")


def test_the_provider_is_registered(tmp_path: Path):
    from filemill.vfs import REGISTRY

    assert isinstance(REGISTRY.get(tmp_path / "x.bundle"), GitBundleProvider)


@pytest.mark.parametrize("operation", ["tree", "blob"])
def test_eviction_during_a_read_keeps_the_repository(bundle, monkeypatch, operation):
    from filemill.providers import gitbundle as gb

    before = (bundle.read_bytes(), bundle.stat())
    gb._repo.cache_clear()
    original = gb._git
    acquired = []

    def evict(repo, *args, **kwargs):
        if args[0] == "ls-tree" or args[:2] == ("cat-file", "blob"):
            acquired.append(repo)
            stat = bundle.stat()
            for offset in range(1, 9):
                gb._repo(str(bundle), stat.st_mtime_ns + offset, stat.st_size)
            assert gb._repo.cache_info().currsize == 8
        return original(repo, *args, **kwargs)

    monkeypatch.setattr(gb, "_git", evict)
    try:
        provider = GitBundleProvider()
        if operation == "tree":
            assert names(provider.list_entries(bundle, "HEAD")) == [
                "docs",
                "src",
                "top.txt",
            ]
        else:
            assert provider.member(bundle, "HEAD/top.txt").data == MEMBERS["top.txt"]
        assert len(acquired) == 1
        assert not acquired[0].exists()
        assert bundle.read_bytes() == before[0]
        assert bundle.stat().st_mtime_ns == before[1].st_mtime_ns
    finally:
        gb._repo.cache_clear()


def test_concurrent_reads_release_the_last_owner(bundle, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event, local

    from filemill.providers import gitbundle as gb

    gb._repo.cache_clear()
    stat = bundle.stat()
    owner = gb._repo(str(bundle), stat.st_mtime_ns, stat.st_size)
    repo_path = Path(owner.name)
    del owner
    ready = [Event(), Event()]
    release = [Event(), Event()]
    original = gb._git
    reader = local()

    def read(index):
        reader.index = index
        return GitBundleProvider().member(bundle, "HEAD/top.txt")

    def pause(repo, *args, **kwargs):
        if args[:2] == ("cat-file", "blob"):
            index = reader.index
            ready[index].set()
            assert release[index].wait(10)
        return original(repo, *args, **kwargs)

    monkeypatch.setattr(gb, "_git", pause)
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="bundle") as pool:
        futures = [pool.submit(read, index) for index in range(2)]
        try:
            assert all(event.wait(10) for event in ready)
            for offset in range(1, 9):
                gb._repo(str(bundle), stat.st_mtime_ns + offset, stat.st_size)
            assert repo_path.exists()
            release[0].set()
            assert futures[0].result(timeout=10).data == MEMBERS["top.txt"]
            assert repo_path.exists()
            release[1].set()
            assert futures[1].result(timeout=10).data == MEMBERS["top.txt"]
            assert not repo_path.exists()
        finally:
            for event in release:
                event.set()
            gb._repo.cache_clear()


@pytest.mark.parametrize("failure", ["exit", "timeout", "oserror"])
@pytest.mark.parametrize("command", ["init", "bundle", "ls-tree"])
def test_git_failures_reach_the_listing_error_field(
    bundle, monkeypatch, failure, command
):
    import json

    from filemill.api import vfs_dir_json
    from filemill.providers import gitbundle as gb

    original = gb.subprocess.run
    failed_repos = []

    def fail(*args, **kwargs):
        if args[0][3] != command:
            return original(*args, **kwargs)
        failed_repos.append(Path(args[0][2]))
        assert kwargs["timeout"] == gb.GIT_TIMEOUT
        assert kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"
        assert kwargs["env"]["GIT_CONFIG_GLOBAL"] == "/dev/null"
        if failure == "timeout":
            raise subprocess.TimeoutExpired(args[0], gb.GIT_TIMEOUT)
        if failure == "oserror":
            raise OSError("cannot execute git")
        return subprocess.CompletedProcess(args[0], 128, b"", b"broken repository")

    gb._repo.cache_clear()
    monkeypatch.setattr(gb.subprocess, "run", fail)
    result = json.loads(vfs_dir_json(bundle, "HEAD").body)
    assert result["entries"] == []
    assert result["denied"]
    assert failed_repos
    if command != "ls-tree":
        assert not failed_repos[0].exists()
    gb._repo.cache_clear()
