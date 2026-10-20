"""Tests for root-relative static serving and the root/directory resource route."""

from starlette.testclient import TestClient

import filemill.app as app_module


def _client(root):
    """Return a TestClient with ROOT pointing at *root*."""
    return TestClient(app_module.app, raise_server_exceptions=False)


# ── GET / – static webserver ───────────────────────────────────────────


def test_resource_serves_file_at_root(tmp_path, monkeypatch):
    """/{path} returns 200 and the file content."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "hello.txt").write_text("hello world")
    resp = _client(tmp_path).get("/hello.txt")
    assert resp.status_code == 200
    assert resp.text == "hello world"


def test_resource_serves_file_via_symlink_bookmark(tmp_path, monkeypatch):
    """/{symlink-name}/{path} resolves through a direct symlink child of ROOT."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "guide.txt").write_text("symlink bookmark")
    root = tmp_path / "menu"
    root.mkdir()
    (root / "coleaders").symlink_to(workspace, target_is_directory=True)
    monkeypatch.setattr(app_module, "ROOT", root)

    resp = _client(root).get("/coleaders/guide.txt")
    assert resp.status_code == 200
    assert resp.text == "symlink bookmark"


def test_resource_404_for_missing_file(tmp_path, monkeypatch):
    """/{path} returns 404 when the file does not exist."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    assert _client(tmp_path).get("/no_such_file.txt").status_code == 404


def test_resource_404_for_missing_directory(tmp_path, monkeypatch):
    """A missing directory returns 404."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "hello.txt").write_text("hello world")
    assert _client(tmp_path).get("/unknown/hello.txt").status_code == 404


def test_resource_correct_content_type_html(tmp_path, monkeypatch):
    """/file.html serves with Content-Type: text/html."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "page.html").write_text("<h1>Hi</h1>")
    resp = _client(tmp_path).get("/page.html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_resource_traversal_denied(tmp_path, monkeypatch):
    """/../etc/passwd is blocked (path escapes ROOT)."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    assert _client(tmp_path).get("/../etc/passwd").status_code == 404


# ── No CORS on resource paths ───────────────────────────────────────────────────────


def test_resource_sends_no_cors_header(tmp_path, monkeypatch):
    """/{path} GET serves the file without Access-Control-Allow-Origin."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    resp = _client(tmp_path).get("/photo.png")
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers


def test_resource_options_is_not_a_cors_preflight(tmp_path, monkeypatch):
    """Resource OPTIONS gets no CORS headers, so another origin cannot read files."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    resp = _client(tmp_path).options("/photo.png")
    assert "access-control-allow-origin" not in resp.headers
    assert "access-control-allow-methods" not in resp.headers


def test_root_serves_index_html_as_is(tmp_path, monkeypatch):
    """A bare root request serves ROOT/index.html as HTML."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    content = "<!doctype html><title>Site index</title>"
    (tmp_path / "index.html").write_text(content)
    resp = _client(tmp_path).get("/")
    assert resp.status_code == 200
    assert resp.text == content
    assert resp.headers["content-type"].startswith("text/html")


def test_root_without_index_html_serves_shared_ui(tmp_path, monkeypatch):
    """A bare root request falls back to the shared directory UI."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    resp = _client(tmp_path).get("/")
    assert resp.status_code == 200
    assert "/ui/entry-server.js" in resp.text
    assert 'data-base="/"' in resp.text


def test_api_query_parameters_reach_starlette_handlers(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    assert _client(tmp_path).get("/api/dir?p=missing").status_code == 404


def test_directory_serves_its_index_html_as_is(tmp_path, monkeypatch):
    """A bare directory URL serves that directory's index.html as HTML."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    site = tmp_path / "site"
    site.mkdir()
    content = "<!doctype html><title>Sub index</title>"
    (site / "index.html").write_text(content)
    resp = _client(tmp_path).get("/site")
    assert resp.status_code == 200
    assert resp.text == content
    assert resp.headers["content-type"].startswith("text/html")


def test_directory_with_a_query_serves_the_listing(tmp_path, monkeypatch):
    """Any query asks for Filemill, so index.html does not take over."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text("sub index")
    resp = _client(tmp_path).get("/site?f&layout=compressed-columns")
    assert resp.status_code == 200
    assert resp.text != "sub index"


def test_directory_without_index_html_serves_the_listing(tmp_path, monkeypatch):
    """A directory with no index.html still gets the shared UI."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "site").mkdir()
    resp = _client(tmp_path).get("/site")
    assert resp.status_code == 200
    assert "/ui/entry-server.js" in resp.text


def test_root_with_short_view_uses_the_resource_route(tmp_path, monkeypatch):
    """?f at the root requests the rendered representation."""
    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    (tmp_path / "index.html").write_text("site index")
    resp = _client(tmp_path).get("/?f&layout=compressed-columns")
    assert resp.status_code == 200
    assert resp.text != "site index"
