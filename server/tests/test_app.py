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


# ── #6 SSE live-reload ────────────────────────────────────────────────────────


def test_sse_reload_returns_404_without_live_mode(client):
    resp = client.get("/sse/reload")
    assert resp.status_code == 404


def test_sse_generator_emits_reload_on_change(monkeypatch, tmp_path):
    """event_generator must yield 'data: reload\\n\\n' when watchfiles reports a change."""
    import asyncio

    monkeypatch.setattr(app_module, "LIVE_MODE", True)
    monkeypatch.setattr(app_module, "ROOT", tmp_path)

    async def one_shot_watch(*_a, **_kw):
        yield {("modified", str(tmp_path / "file.txt"))}

    import watchfiles

    monkeypatch.setattr(watchfiles, "awatch", one_shot_watch)

    async def run():
        from starlette.responses import StreamingResponse

        resp = await app_module.sse_reload()
        assert isinstance(resp, StreamingResponse)
        first = await resp.body_iterator.__anext__()
        # Exhaust the generator so the loop-exit branch is covered.
        try:
            await resp.body_iterator.__anext__()
        except StopAsyncIteration:
            pass
        return first

    assert asyncio.run(run()) == "data: reload\n\n"


def test_sse_generator_keepalive_on_watchfiles_error(monkeypatch, tmp_path):
    """When watchfiles raises, event_generator must fall back to keepalive pings."""
    import asyncio

    monkeypatch.setattr(app_module, "LIVE_MODE", True)
    monkeypatch.setattr(app_module, "ROOT", tmp_path)

    async def broken_watch(*_a, **_kw):
        raise RuntimeError("watchfiles unavailable")
        yield  # pragma: no cover – makes it an async generator

    import watchfiles

    monkeypatch.setattr(watchfiles, "awatch", broken_watch)

    sleep_durations: list[float] = []

    async def fast_sleep(n: float) -> None:
        sleep_durations.append(n)

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    async def run():
        from starlette.responses import StreamingResponse

        resp = await app_module.sse_reload()
        assert isinstance(resp, StreamingResponse)
        first = await resp.body_iterator.__anext__()
        return first

    result = asyncio.run(run())
    assert result == ": keepalive\n\n"
    assert sleep_durations == [30]


def test_sse_reload_exists_with_live_mode(monkeypatch):
    """sse_reload() must return a StreamingResponse (not a 404 Response) in live mode.

    Calling the async handler directly via asyncio.run() avoids making any real
    HTTP request against the infinite SSE stream, which would hang the test suite
    regardless of the timeout strategy used (see issue #17).
    """
    import asyncio

    from starlette.responses import StreamingResponse

    import filemill.app as app_module

    monkeypatch.setattr(app_module, "LIVE_MODE", True)
    result = asyncio.run(app_module.sse_reload())
    assert isinstance(result, StreamingResponse)


def test_live_reload_js_in_styles():
    from filemill.styles import LIVE_RELOAD_JS

    assert "EventSource" in LIVE_RELOAD_JS
    assert "/sse/reload" in LIVE_RELOAD_JS


# ── settings-menu version ─────────────────────────────────────────────────────


def test_settings_version_matches_pyproject():
    """The version constant in shell.js tracks pyproject.toml."""
    import tomllib
    from pathlib import Path

    pkg = Path(app_module.__file__).parent
    pyproject = pkg.parent.parent / "pyproject.toml"
    version = tomllib.loads(pyproject.read_text())["project"]["version"]
    assert f"Filemill {version}" in (pkg / "ui" / "core" / "shell.js").read_text()
