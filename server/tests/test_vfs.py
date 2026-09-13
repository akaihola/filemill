"""Tests for filemill.vfs – VFSEntry, VFSRegistry, VFSProvider protocol, is_vfs_file."""

from __future__ import annotations

from pathlib import Path

# ── _truncate ─────────────────────────────────────────────────────────────────


def test_truncate_short_string_unchanged():
    from filemill.vfs import _truncate

    assert _truncate("hello") == "hello"


def test_truncate_long_string_at_60_chars():
    from filemill.vfs import _truncate

    s = "x" * 70
    result = _truncate(s)
    assert len(result) == 60
    assert result.endswith("…")


def test_truncate_exactly_60_unchanged():
    from filemill.vfs import _truncate

    assert _truncate("x" * 60) == "x" * 60


# ── VFSEntry ──────────────────────────────────────────────────────────────────


def test_vfs_entry_fields():
    from filemill.vfs import VFSEntry

    e = VFSEntry(name="users", vpath="users", is_folder=True, icon="📁")
    assert e.name == "users"
    assert e.vpath == "users"
    assert e.is_folder is True
    assert e.icon == "📁"


# ── VFSRegistry ───────────────────────────────────────────────────────────────


def test_vfs_registry_get_returns_none_when_empty():
    from filemill.vfs import VFSRegistry

    reg = VFSRegistry()
    assert reg.get(Path("foo.db")) is None


def test_vfs_registry_register_and_get_returns_provider():
    from filemill.vfs import VFSRegistry

    class FakeProvider:
        def handles(self, path: Path) -> bool:
            return path.suffix.lower() == ".db"

        def list_entries(self, path, vpath):
            return []

        def render_preview(self, path, vpath, fmt, page, limit, col=0):
            return ""

        def default_fmt(self, vpath):
            return "folders"

    reg = VFSRegistry()
    fp = FakeProvider()
    reg.register(fp)
    assert reg.get(Path("foo.db")) is fp


def test_vfs_registry_get_returns_none_for_unmatched():
    from filemill.vfs import VFSRegistry

    class FakeProvider:
        def handles(self, path: Path) -> bool:
            return path.suffix.lower() == ".db"

        def list_entries(self, path, vpath):
            return []

        def render_preview(self, path, vpath, fmt, page, limit, col=0):
            return ""

        def default_fmt(self, vpath):
            return "folders"

    reg = VFSRegistry()
    reg.register(FakeProvider())
    assert reg.get(Path("foo.csv")) is None


def test_vfs_registry_last_registered_wins():
    from filemill.vfs import VFSRegistry

    class Provider1:
        def handles(self, path: Path) -> bool:
            return path.suffix.lower() == ".db"

        def list_entries(self, path, vpath):
            return []

        def render_preview(self, path, vpath, fmt, page, limit, col=0):
            return ""

        def default_fmt(self, vpath):
            return "folders"

    class Provider2(Provider1):
        pass

    reg = VFSRegistry()
    p1, p2 = Provider1(), Provider2()
    reg.register(p1)
    reg.register(p2)
    assert reg.get(Path("x.db")) is p2


# ── VFSProvider protocol ───────────────────────────────────────────────────────


def test_vfs_provider_protocol_is_runtime_checkable():
    from filemill.vfs import VFSProvider

    class FakeProvider:
        def handles(self, path: Path) -> bool:
            return True

        def list_entries(self, path, vpath):
            return []

        def render_preview(self, path, vpath, fmt, page, limit, col=0):
            return ""

        def default_fmt(self, vpath):
            return ""

    assert isinstance(FakeProvider(), VFSProvider)


# ── is_vfs_file ───────────────────────────────────────────────────────────────


def test_is_vfs_file_returns_true_for_db(tmp_path):
    from filemill.vfs import is_vfs_file

    f = tmp_path / "data.db"
    f.touch()
    assert is_vfs_file(f) is True


def test_is_vfs_file_returns_false_for_txt(tmp_path):
    from filemill.vfs import is_vfs_file

    f = tmp_path / "data.txt"
    f.touch()
    assert is_vfs_file(f) is False


# ── Stub provider registration ────────────────────────────────────────────────


def test_csv_provider_registered(tmp_path):
    from filemill.vfs import REGISTRY

    f = tmp_path / "data.csv"
    f.touch()
    provider = REGISTRY.get(f)
    assert provider is not None


def test_csv_provider_default_fmt_is_spreadsheet(tmp_path):
    from filemill.vfs import REGISTRY

    f = tmp_path / "data.csv"
    f.touch()
    provider = REGISTRY.get(f)
    assert provider.default_fmt("") == "spreadsheet"


def test_json_provider_registered(tmp_path):
    from filemill.vfs import REGISTRY

    f = tmp_path / "data.json"
    f.touch()
    provider = REGISTRY.get(f)
    assert provider is not None


def test_json_provider_default_fmt_is_formatted(tmp_path):
    from filemill.vfs import REGISTRY

    f = tmp_path / "data.json"
    f.touch()
    provider = REGISTRY.get(f)
    assert provider.default_fmt("") == "formatted"
