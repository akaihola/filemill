from unittest.mock import MagicMock

import filemill.app as app_module
from filemill.paths import resolve_safe

# ── _resolve_safe ─────────────────────────────────────────────────────────────


def test_resolve_safe_valid_path(tmp_path):
    f = tmp_path / "file.txt"
    f.touch()
    assert resolve_safe(str(f), tmp_path) == f.resolve()


def test_resolve_safe_traversal_returns_none(tmp_path):
    outside = str(tmp_path / ".." / "outside.txt")
    assert resolve_safe(outside, tmp_path) is None


def test_resolve_safe_exception_returns_none():
    """root.resolve() raises → outer except catches it → returns None."""
    mock_root = MagicMock()
    mock_root.resolve.side_effect = RuntimeError("bad root")
    assert resolve_safe("/some/path", mock_root) is None


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
