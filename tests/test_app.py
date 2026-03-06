from unittest.mock import MagicMock
from urllib.parse import quote

import pykofinder.app as app_module
from pykofinder.app import _resolve_safe, _parse_desktop_url


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
    assert "pykofinder" in resp.text


# ── GET /click ────────────────────────────────────────────────────────────────


def test_click_directory_returns_new_column(client, tmp_root):
    subdir = tmp_root / "subdir"
    resp = client.get(f"/click?path={quote(str(subdir))}&col=1")
    assert resp.status_code == 200
    assert "col-1" in resp.text


def test_click_file_returns_preview(client, tmp_root):
    md_file = tmp_root / "readme.md"
    resp = client.get(f"/click?path={quote(str(md_file))}&col=1")
    assert resp.status_code == 200
    assert "preview-md" in resp.text


def test_click_bad_path_returns_access_denied(client):
    resp = client.get(f"/click?path={quote('/etc/passwd')}&col=1")
    assert resp.status_code == 200
    assert "Access denied" in resp.text


def test_click_render_preview_exception_returns_error_html(
    client, tmp_root, monkeypatch
):
    monkeypatch.setattr(
        "pykofinder.app.render_preview",
        MagicMock(side_effect=RuntimeError("boom")),
    )
    md_file = tmp_root / "readme.md"
    resp = client.get(f"/click?path={quote(str(md_file))}&col=1")
    assert resp.status_code == 200
    assert "preview-error" in resp.text


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


# ── breadcrumb OOB ────────────────────────────────────────────────────────────


def test_click_directory_includes_breadcrumb_oob(client, tmp_root):
    from urllib.parse import quote

    subdir = tmp_root / "subdir"
    resp = client.get(f"/click?path={quote(str(subdir))}&col=1")
    assert resp.status_code == 200
    assert "hx-swap-oob" in resp.text
    assert "breadcrumb" in resp.text


def test_click_file_includes_breadcrumb_oob(client, tmp_root):
    from urllib.parse import quote

    md_file = tmp_root / "readme.md"
    resp = client.get(f"/click?path={quote(str(md_file))}&col=1")
    assert resp.status_code == 200
    assert "breadcrumb" in resp.text


# ── GET /restore ──────────────────────────────────────────────────────────────


def test_restore_valid_directory_returns_200(client, tmp_root):
    from urllib.parse import quote

    subdir = tmp_root / "subdir"
    resp = client.get(f"/restore?path={quote(str(subdir))}")
    assert resp.status_code == 200
    assert 'id="finder"' in resp.text
    assert "col-0" in resp.text


def test_restore_valid_file_includes_preview(client, tmp_root):
    from urllib.parse import quote

    md = tmp_root / "readme.md"
    resp = client.get(f"/restore?path={quote(str(md))}")
    assert resp.status_code == 200
    assert "preview-md" in resp.text


def test_restore_bad_path_returns_root_view(client, tmp_root):
    from urllib.parse import quote

    resp = client.get(f"/restore?path={quote('/etc/passwd')}")
    assert resp.status_code == 200
    assert "finder" in resp.text


def test_restore_zone2_symlink_path(tmp_path, monkeypatch):
    """restore() must not crash when _resolve_safe returns a zone-2 path
    that raises ValueError on p.relative_to(ROOT)."""
    import tempfile
    from pathlib import Path
    from urllib.parse import quote
    from starlette.testclient import TestClient

    # Outer dir simulates a target outside ROOT
    with tempfile.TemporaryDirectory() as outside:
        outside_path = Path(outside)
        (outside_path / "zone2.txt").write_text("zone2 content\n")
        # Symlink inside ROOT → outside dir (zone-2 bookmark)
        bookmark = tmp_path / "bookmark"
        bookmark.symlink_to(outside_path)
        monkeypatch.setattr(app_module, "ROOT", tmp_path)
        c = TestClient(app_module.app, raise_server_exceptions=False)
        # Request the file inside the zone-2 target
        resp = c.get(f"/restore?path={quote(str(outside_path / 'zone2.txt'))}")
        assert resp.status_code == 200
        assert "finder" in resp.text


def test_restore_render_preview_exception_handled(client, tmp_root, monkeypatch):
    """render_preview() raising inside restore() must produce a preview-error div."""
    from urllib.parse import quote

    monkeypatch.setattr(
        app_module,
        "render_preview",
        lambda _p: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    md = tmp_root / "readme.md"
    resp = client.get(f"/restore?path={quote(str(md))}")
    assert resp.status_code == 200
    assert "preview-error" in resp.text


def test_url_sync_js_in_column_js():
    from pykofinder.styles import COLUMN_JS

    assert "pushState" in COLUMN_JS
    assert "_pendingPath" in COLUMN_JS or "pendingPath" in COLUMN_JS.lower()


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
    import pykofinder.app as app_module
    from starlette.responses import StreamingResponse

    monkeypatch.setattr(app_module, "LIVE_MODE", True)
    result = asyncio.run(app_module.sse_reload())
    assert isinstance(result, StreamingResponse)


def test_live_reload_js_in_styles():
    from pykofinder.styles import LIVE_RELOAD_JS

    assert "EventSource" in LIVE_RELOAD_JS
    assert "/sse/reload" in LIVE_RELOAD_JS


# ── #15 Keyboard navigation ───────────────────────────────────────────────────


def test_keyboard_nav_js_in_column_js():
    from pykofinder.styles import COLUMN_JS

    assert "ArrowDown" in COLUMN_JS
    assert "ArrowUp" in COLUMN_JS
    assert "ArrowRight" in COLUMN_JS
    assert "ArrowLeft" in COLUMN_JS
