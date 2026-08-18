"""Tests for _resolve_safe access-control logic.

Directory layout created per test (via tmp_path):

    ROOT/
        real_file.txt
        real_dir/
            nested_file.txt
            inner_link -> ROOT/real_dir/nested_file.txt   (safe: stays in subtree)
        bookmark -> /outside/dirA/                        (zone-2 symlink)

    /outside/
        dirA/
            file_in_A.txt
            safe_link  -> /outside/dirA/file_in_A.txt    (safe: stays in dirA)
            cross_link -> /outside/dirB/file_in_B.txt    (unsafe: escapes dirA)
            root_link  -> ROOT/real_file.txt              (safe: target in zone 1)
        dirB/
            file_in_B.txt
"""

import pytest

from filemill.app import _resolve_safe


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def resolve(root, path_str):
    """Convenience wrapper that injects a custom root."""
    return _resolve_safe(path_str, root=root)


# ---------------------------------------------------------------------------
# fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def tree(tmp_path):
    """Build the directory tree described in the module docstring."""
    root = tmp_path / "ROOT"
    outside = tmp_path / "outside"

    # ROOT internals
    root.mkdir()
    (root / "real_file.txt").write_text("hello")
    real_dir = root / "real_dir"
    real_dir.mkdir()
    nested = real_dir / "nested_file.txt"
    nested.write_text("nested")

    # safe symlink inside real_dir – points within real_dir
    (real_dir / "inner_link").symlink_to(nested)

    # Outside directories
    dir_a = outside / "dirA"
    dir_b = outside / "dirB"
    dir_a.mkdir(parents=True)
    dir_b.mkdir(parents=True)
    file_a = dir_a / "file_in_A.txt"
    file_b = dir_b / "file_in_B.txt"
    file_a.write_text("A")
    file_b.write_text("B")

    # Symlinks inside dirA
    (dir_a / "safe_link").symlink_to(file_a)  # stays inside dirA  ✓
    (dir_a / "cross_link").symlink_to(file_b)  # escapes to dirB   ✗
    (dir_a / "root_link").symlink_to(root / "real_file.txt")  # into zone 1  ✓

    # Zone-2 bookmark in ROOT
    (root / "bookmark").symlink_to(dir_a)

    return {"root": root, "outside": outside, "dir_a": dir_a, "dir_b": dir_b}


# ---------------------------------------------------------------------------
# Zone 1 – paths that live under ROOT
# ---------------------------------------------------------------------------


def test_root_itself(tree):
    root = tree["root"]
    assert resolve(root, str(root)) == root.resolve()


def test_real_file_in_root(tree):
    root = tree["root"]
    p = root / "real_file.txt"
    assert resolve(root, str(p)) == p.resolve()


def test_real_directory_in_root(tree):
    root = tree["root"]
    p = root / "real_dir"
    assert resolve(root, str(p)) == p.resolve()


def test_file_inside_real_subdirectory(tree):
    root = tree["root"]
    p = root / "real_dir" / "nested_file.txt"
    assert resolve(root, str(p)) == p.resolve()


def test_safe_symlink_inside_real_dir_stays_in_zone1(tree):
    """A symlink within a real ROOT subdirectory whose target is also in ROOT."""
    root = tree["root"]
    link = root / "real_dir" / "inner_link"
    result = resolve(root, str(link))
    assert result == link.resolve()
    assert result == (root / "real_dir" / "nested_file.txt").resolve()


# ---------------------------------------------------------------------------
# Zone 2 – paths reachable via a direct bookmark symlink in ROOT
# ---------------------------------------------------------------------------


def test_bookmark_symlink_entry_itself(tree):
    """The bookmark symlink entry in ROOT is allowed and resolves to its target."""
    root = tree["root"]
    dir_a = tree["dir_a"]
    result = resolve(root, str(root / "bookmark"))
    assert result == dir_a.resolve()


def test_file_inside_bookmark_target(tree):
    """A real file inside the bookmark target directory is allowed."""
    root = tree["root"]
    dir_a = tree["dir_a"]
    result = resolve(root, str(dir_a / "file_in_A.txt"))
    assert result == (dir_a / "file_in_A.txt").resolve()


def test_safe_symlink_inside_bookmark_stays_in_zone2(tree):
    """A symlink within the bookmark dir whose target is also within that dir."""
    root = tree["root"]
    dir_a = tree["dir_a"]
    result = resolve(root, str(dir_a / "safe_link"))
    assert result == (dir_a / "file_in_A.txt").resolve()


def test_symlink_inside_bookmark_pointing_into_zone1(tree):
    """A symlink in the bookmark dir pointing back into ROOT (zone 1) is allowed."""
    root = tree["root"]
    dir_a = tree["dir_a"]
    result = resolve(root, str(dir_a / "root_link"))
    assert result == (root / "real_file.txt").resolve()


# ---------------------------------------------------------------------------
# Denied – paths that escape all allowed zones
# ---------------------------------------------------------------------------


def test_path_entirely_outside_root(tree):
    """An absolute path that is not under ROOT and not a bookmark target."""
    root = tree["root"]
    dir_b = tree["dir_b"]
    assert resolve(root, str(dir_b / "file_in_B.txt")) is None


def test_symlink_inside_bookmark_escaping_to_outside(tree):
    """A symlink in the bookmark dir whose target escapes to an unrelated dir."""
    root = tree["root"]
    dir_a = tree["dir_a"]
    assert resolve(root, str(dir_a / "cross_link")) is None


# ---------------------------------------------------------------------------
# Path-traversal attacks
# ---------------------------------------------------------------------------


def test_traversal_from_root_via_dotdot(tree):
    root = tree["root"]
    assert (
        resolve(root, str(root / ".." / "outside" / "dirB" / "file_in_B.txt")) is None
    )


def test_traversal_from_bookmark_via_dotdot(tree):
    root = tree["root"]
    dir_a = tree["dir_a"]
    # Construct a path that starts inside dirA but climbs out via ..
    evil = dir_a / ".." / "dirB" / "file_in_B.txt"
    assert resolve(root, str(evil)) is None


def test_traversal_to_etc(tree):
    root = tree["root"]
    assert resolve(root, str(root / ".." / ".." / ".." / "etc" / "passwd")) is None


# ---------------------------------------------------------------------------
# URL-encoding
# ---------------------------------------------------------------------------


def test_url_encoded_path_is_decoded(tree):
    """Percent-encoded slashes and spaces in the path string are handled."""
    root = tree["root"]
    # Encode the path manually: spaces become %20
    spaced_dir = root / "dir with spaces"
    spaced_dir.mkdir()
    (spaced_dir / "f.txt").write_text("x")
    encoded_path = str(spaced_dir / "f.txt").replace(" ", "%20")
    result = resolve(root, encoded_path)
    assert result == (spaced_dir / "f.txt").resolve()


# ---------------------------------------------------------------------------
# startswith prefix-collision guard
# ---------------------------------------------------------------------------


def test_sibling_dir_with_longer_name_is_denied(tree):
    """ROOT-sibling directory whose name starts with ROOT's name must be denied.

    e.g. ROOT=/tmp/abc  and path=/tmp/abcEVIL/file – a naive startswith check
    would incorrectly allow this.
    """
    root = tree["root"]
    sibling = root.parent / (root.name + "EVIL")
    sibling.mkdir()
    (sibling / "evil.txt").write_text("bad")
    assert resolve(root, str(sibling / "evil.txt")) is None
