from unittest.mock import MagicMock

import filemill.app as app_module
from filemill.app import _resolve_safe

# ── _resolve_safe ─────────────────────────────────────────────────────────────


def test_resolve_safe_valid_path(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    f = tmp_path / "file.txt"
    f.touch()
    assert _resolve_safe(str(f)) == f.resolve()


def test_resolve_safe_traversal_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    outside = str(tmp_path / ".." / "outside.txt")
    assert _resolve_safe(outside) is None


def test_resolve_safe_exception_returns_none(tmp_path, monkeypatch):
    """ROOT.resolve() raises → outer except catches it → returns None."""
    mock_root = MagicMock()
    mock_root.resolve.side_effect = RuntimeError("bad root")
    monkeypatch.setattr(app_module, "ROOT", mock_root)
    assert _resolve_safe("/some/path") is None


# ── GET / ─────────────────────────────────────────────────────────────────────


def test_index_returns_200_with_title(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "filemill" in resp.text


def test_obsolete_raw_route_is_removed(client):
    assert client.get("/raw?path=readme.md").status_code == 404


# ── settings-menu version ─────────────────────────────────────────────────────


def test_settings_version_matches_pyproject():
    """The version constant in shell.js tracks pyproject.toml."""
    import tomllib
    from pathlib import Path

    pkg = Path(app_module.__file__).parent
    pyproject = pkg.parent.parent / "pyproject.toml"
    version = tomllib.loads(pyproject.read_text())["project"]["version"]
    assert f"Filemill {version}" in (pkg / "ui" / "core" / "shell.js").read_text()
