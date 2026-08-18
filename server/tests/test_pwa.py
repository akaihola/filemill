"""Tests for PWA assets: manifest, service worker, icons, and head tags."""


# ── manifest.json ─────────────────────────────────────────────────────────────


def test_manifest_status(client):
    resp = client.get("/manifest.json")
    assert resp.status_code == 200


def test_manifest_content_type(client):
    resp = client.get("/manifest.json")
    assert (
        "manifest" in resp.headers["content-type"]
        or "json" in resp.headers["content-type"]
    )


def test_manifest_valid_json(client):
    resp = client.get("/manifest.json")
    data = resp.json()
    assert isinstance(data, dict)


def test_manifest_required_fields(client):
    data = client.get("/manifest.json").json()
    assert data["name"] == "filemill"
    assert data["start_url"] == "/f/"
    assert data["display"] == "standalone"
    assert isinstance(data["icons"], list)
    assert len(data["icons"]) >= 1


def test_manifest_has_192_icon(client):
    data = client.get("/manifest.json").json()
    sizes = {icon["sizes"] for icon in data["icons"]}
    assert "192x192" in sizes


def test_manifest_has_512_icon(client):
    data = client.get("/manifest.json").json()
    sizes = {icon["sizes"] for icon in data["icons"]}
    assert "512x512" in sizes


# ── sw.js ─────────────────────────────────────────────────────────────────────


def test_sw_status(client):
    assert client.get("/sw.js").status_code == 200


def test_sw_content_type(client):
    ct = client.get("/sw.js").headers["content-type"]
    assert "javascript" in ct


def test_sw_allowed_header(client):
    resp = client.get("/sw.js")
    assert resp.headers.get("service-worker-allowed") == "/"


def test_sw_contains_cache_name(client):
    body = client.get("/sw.js").text
    assert "filemill" in body


# ── icons ─────────────────────────────────────────────────────────────────────


def test_icon_192_status(client):
    assert client.get("/icons/icon-192.png").status_code == 200


def test_icon_512_status(client):
    assert client.get("/icons/icon-512.png").status_code == 200


def test_icon_svg_status(client):
    assert client.get("/icons/icon.svg").status_code == 200


def test_icon_unknown_returns_404(client):
    assert client.get("/icons/does-not-exist.png").status_code == 404


def test_icon_traversal_blocked():
    """Path(name).name strips directory components so traversal cannot escape icons/."""
    # Starlette normalises "/icons/../manifest.json" → "/manifest.json" at the
    # routing layer, so the icon handler never receives ".." in `name` via HTTP.
    # The defence-in-depth is that Path(name).name strips any remaining slashes.
    from pathlib import Path

    from filemill.app import _STATIC_DIR

    # Simulate what the handler does with a worst-case name.
    safe = Path("../manifest.json").name  # → "manifest.json"
    resolved = _STATIC_DIR / "icons" / safe
    # "manifest.json" does not exist inside icons/, so the handler would 404.
    assert not resolved.exists()


# ── app shell head tags ───────────────────────────────────────────────────────


def test_shell_has_manifest_link(client):
    html = client.get("/f/").text
    assert 'rel="manifest"' in html
    assert "/manifest.json" in html


def test_shell_has_theme_color(client):
    html = client.get("/f/").text
    assert 'name="theme-color"' in html


def test_shell_has_viewport_meta(client):
    html = client.get("/f/").text
    assert 'name="viewport"' in html


def test_shell_has_apple_touch_icon(client):
    html = client.get("/f/").text
    assert 'rel="apple-touch-icon"' in html


def test_shell_registers_sw(client):
    html = client.get("/f/").text
    assert "serviceWorker" in html
    assert "/sw.js" in html
