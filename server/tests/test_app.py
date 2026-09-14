from unittest.mock import MagicMock
from urllib.parse import quote

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


# ── GET /raw ──────────────────────────────────────────────────────────────────


def test_raw_valid_file_returns_200(client, tmp_root):
    md_file = tmp_root / "readme.md"
    resp = client.get(f"/raw?path={quote(str(md_file))}")
    assert resp.status_code == 200


def test_raw_bad_path_returns_404(client):
    resp = client.get(f"/raw?path={quote('/etc/shadow')}")
    assert resp.status_code == 404


def test_raw_directory_returns_404(client, tmp_root):
    """p.is_file() is False for a directory → 404."""
    resp = client.get(f"/raw?path={quote(str(tmp_root / 'subdir'))}")
    assert resp.status_code == 404


# ── settings-menu version ─────────────────────────────────────────────────────


def test_settings_version_matches_pyproject():
    """The version constant in shell.js tracks pyproject.toml."""
    import tomllib
    from pathlib import Path

    pkg = Path(app_module.__file__).parent
    pyproject = pkg.parent.parent / "pyproject.toml"
    version = tomllib.loads(pyproject.read_text())["project"]["version"]
    assert f"Filemill {version}" in (pkg / "ui" / "core" / "shell.js").read_text()
