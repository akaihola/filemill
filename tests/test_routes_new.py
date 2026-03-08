"""Tests for issues #23 (/w/ static server, /f/ finder view, #21 mermaid CDN)."""

from urllib.parse import quote

import pykofinder.app as app_module
from starlette.testclient import TestClient


def _client(root):
    """Return a TestClient with ROOT pointing at *root*."""
    return TestClient(app_module.app, raise_server_exceptions=False)


# ── #23 GET /w/ – static webserver ───────────────────────────────────────────


def test_web_static_serves_file(tmp_path, monkeypatch):
    """/w/{path} returns 200 and the file content."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "hello.txt").write_text("hello world")
    resp = _client(tmp_path).get("/w/hello.txt")
    assert resp.status_code == 200
    assert resp.text == "hello world"


def test_web_static_404_for_missing_file(tmp_path, monkeypatch):
    """/w/{path} returns 404 when the file does not exist."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    assert _client(tmp_path).get("/w/no_such_file.txt").status_code == 404


def test_web_static_correct_content_type_html(tmp_path, monkeypatch):
    """/w/file.html serves with Content-Type: text/html."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "page.html").write_text("<h1>Hi</h1>")
    resp = _client(tmp_path).get("/w/page.html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_web_static_traversal_denied(tmp_path, monkeypatch):
    """/w/../etc/passwd is blocked (path escapes ROOT)."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    assert _client(tmp_path).get("/w/../etc/passwd").status_code == 404


# ── #38 CORS on /w/ ──────────────────────────────────────────────────────────


def test_web_static_cors_header_present(tmp_path, monkeypatch):
    """/w/{path} GET response carries Access-Control-Allow-Origin: *."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    resp = _client(tmp_path).get("/w/photo.png")
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"


def test_web_static_cors_methods_header(tmp_path, monkeypatch):
    """/w/ GET response advertises GET and OPTIONS in Access-Control-Allow-Methods."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "doc.txt").write_text("hi")
    resp = _client(tmp_path).get("/w/doc.txt")
    methods = resp.headers.get("access-control-allow-methods", "")
    assert "GET" in methods
    assert "OPTIONS" in methods


def test_web_static_options_preflight_200(tmp_path, monkeypatch):
    """/w/ OPTIONS preflight returns 200 with CORS headers."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    resp = _client(tmp_path).options("/w/photo.png")
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"


def test_web_static_options_allow_headers(tmp_path, monkeypatch):
    """/w/ OPTIONS preflight echoes Access-Control-Allow-Headers: *."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    resp = _client(tmp_path).options("/w/photo.png")
    assert resp.headers.get("access-control-allow-headers") == "*"


def test_web_static_cors_not_on_other_routes(tmp_path, monkeypatch):
    """/f/ and other routes do NOT carry Access-Control-Allow-Origin."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    resp = _client(tmp_path).get("/f/")
    assert resp.headers.get("access-control-allow-origin") is None


# ── #23 GET /f/ – finder deep-link ────────────────────────────────────────────


def test_finder_view_serves_shell_with_deep_link_script(tmp_path, monkeypatch):
    """/f/{path} returns the full app shell with an inline _deepNavigate call."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "readme.md").touch()
    resp = _client(tmp_path).get("/f/readme.md")
    assert resp.status_code == 200
    body = resp.text
    assert "pykofinder" in body
    assert "_deepNavigate" in body
    assert "readme.md" in body


def test_finder_view_root_serves_shell(tmp_path, monkeypatch):
    """/f/ (no path) returns the full app shell without an inline deep-link call."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    resp = _client(tmp_path).get("/f/")
    assert resp.status_code == 200
    body = resp.text
    assert "pykofinder" in body
    # The inline nav script uses no-space 'DOMContentLoaded',function() pattern.
    # COLUMN_JS uses 'DOMContentLoaded', function() with a space – different.
    assert "'DOMContentLoaded',function()" not in body


def test_root_redirects_to_finder(tmp_path, monkeypatch):
    """GET / redirects to /f/."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    c = TestClient(
        app_module.app, raise_server_exceptions=False, follow_redirects=False
    )
    resp = c.get("/")
    assert resp.status_code == 302
    assert resp.headers.get("location", "").startswith("/f/")


def test_finder_view_404_for_missing(tmp_path, monkeypatch):
    """/f/{path} returns 404 when the path is outside ROOT."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    assert _client(tmp_path).get("/f/no_such_thing.md").status_code == 404


# ── #23 HTML preview – "View as web page" button ─────────────────────────────


def test_html_preview_has_webmode_button(tmp_path, monkeypatch):
    """Clicking an HTML file injects a '🌐 View as web page' link."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    f = tmp_path / "index.html"
    f.write_text("<h1>Hello</h1>")
    resp = _client(tmp_path).get(f"/click?path={quote(str(f))}&col=1")
    assert resp.status_code == 200
    body = resp.text
    assert "/w/" in body
    assert "🌐" in body or "web page" in body.lower()


def test_htm_preview_has_webmode_button(tmp_path, monkeypatch):
    """.htm files also get the 'View as web page' button."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    f = tmp_path / "page.htm"
    f.write_text("<p>hi</p>")
    resp = _client(tmp_path).get(f"/click?path={quote(str(f))}&col=1")
    assert resp.status_code == 200
    assert "/w/" in resp.text


def test_non_html_preview_no_webmode_button(tmp_path, monkeypatch):
    """Non-HTML file previews do NOT have the 'View as web page' button."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    f = tmp_path / "readme.md"
    f.write_text("# Hello")
    resp = _client(tmp_path).get(f"/click?path={quote(str(f))}&col=1")
    assert resp.status_code == 200
    assert "preview-webmode-bar" not in resp.text


# ── #21 mermaid CDN in page head ─────────────────────────────────────────────


def test_mermaid_js_in_page_head(tmp_path, monkeypatch):
    """The app index page includes a mermaid.js CDN script tag."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    resp = _client(tmp_path).get("/")
    assert resp.status_code == 200
    assert "mermaid" in resp.text.lower()


def test_mermaid_js_cdn_url_present(tmp_path, monkeypatch):
    """The mermaid CDN URL is in the page source."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    resp = _client(tmp_path).get("/")
    assert "cdn.jsdelivr.net" in resp.text
    assert "mermaid" in resp.text
