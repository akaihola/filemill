from unittest.mock import MagicMock
from urllib.parse import quote

import filemill.app as app_module
from filemill.app import _parse_desktop_url, _resolve_safe

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


# ── _parse_desktop_url ────────────────────────────────────────────────────────


def test_parse_desktop_url_link_type(tmp_path):
    f = tmp_path / "link.desktop"
    f.write_text("[Desktop Entry]\nType=Link\nURL=https://example.com\n")
    assert _parse_desktop_url(f) == "https://example.com"


def test_parse_desktop_url_non_link_returns_none(tmp_path):
    f = tmp_path / "app.desktop"
    f.write_text("[Desktop Entry]\nType=Application\n")
    assert _parse_desktop_url(f) is None


def test_parse_desktop_url_no_section_returns_none(tmp_path):
    f = tmp_path / "bad.desktop"
    f.write_text("[Other]\nFoo=bar\n")
    assert _parse_desktop_url(f) is None


def test_parse_desktop_url_empty_url_returns_none(tmp_path):
    f = tmp_path / "link.desktop"
    f.write_text("[Desktop Entry]\nType=Link\nURL=\n")
    assert _parse_desktop_url(f) is None


def test_parse_desktop_url_exception_returns_none(tmp_path, monkeypatch):
    f = tmp_path / "link.desktop"
    f.touch()
    import configparser as cp_mod

    def boom(self, *a, **kw):
        raise RuntimeError("fail")

    monkeypatch.setattr(cp_mod.ConfigParser, "read", boom)
    assert _parse_desktop_url(f) is None


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


# ── GET /open-link ────────────────────────────────────────────────────────────


def test_open_link_valid_redirects_302(client, tmp_root):
    desktop = tmp_root / "link.desktop"
    resp = client.get(f"/open-link?path={quote(str(desktop))}", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "https://example.com"


def test_open_link_bad_path_returns_404(client):
    resp = client.get(f"/open-link?path={quote('/etc/passwd')}")
    assert resp.status_code == 404


def test_open_link_not_link_type_returns_400(client, tmp_root):
    app_desktop = tmp_root / "app.desktop"
    app_desktop.write_text("[Desktop Entry]\nType=Application\nName=App\n")
    resp = client.get(f"/open-link?path={quote(str(app_desktop))}")
    assert resp.status_code == 400


# ── settings-menu version ─────────────────────────────────────────────────────


def test_settings_version_matches_pyproject():
    """The version constant in shell.js tracks pyproject.toml."""
    import tomllib
    from pathlib import Path

    pkg = Path(app_module.__file__).parent
    pyproject = pkg.parent.parent / "pyproject.toml"
    version = tomllib.loads(pyproject.read_text())["project"]["version"]
    assert f"Filemill {version}" in (pkg / "ui" / "core" / "shell.js").read_text()
