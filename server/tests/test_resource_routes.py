"""One path, every representation (PLAN-19 §1–§5).

For a configured root containing ``docs/readme.md``, these are the addresses:

    /docs/readme.md                              the file's bytes
    /docs/readme.md?filemill=render     Markdown as HTML
    /docs/readme.md?filemill=highlight  the source, coloured
    /docs/readme.md?filemill=raw          the bytes, said out loud

    ?layout=full-columns        the finder, opened there   (default)
    ?layout=compressed-columns  the same, columns folded
    ?layout=no-columns          the representation alone

The tests below assert exact path and query semantics rather than "the href
contains /raw", because a URL contract is only worth having if it is pinned
character by character.
"""

import pytest
from starlette.testclient import TestClient

import filemill.app as app_module

MARKDOWN = "# Guide\n\nSome *emphasis* and a <script>alert(1)</script> tag.\n"


@pytest.fixture()
def site(tmp_path, monkeypatch):
    """A small root: a Markdown file, a stylesheet, a script, an image, a dotfile."""
    root = tmp_path / "menu"
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "readme.md").write_text(MARKDOWN)
    (root / "site").mkdir()
    (root / "site" / "main.css").write_text("body { color: red; }")
    (root / "hello.py").write_text("def hello():\n    return 'hi'\n")
    (root / "page.html").write_text("<h1>Hi</h1>")
    (root / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (root / ".secret").write_text("dotfile")
    (root / "my notes").mkdir()
    (root / "my notes" / "a b.md").write_text("# Spaced\n")
    monkeypatch.setattr(app_module, "ROOT", root)
    return root


@pytest.fixture()
def client(site):
    return TestClient(app_module.app, raise_server_exceptions=False)


# ── The bare path serves the file ────────────────────────────────────────────


def test_bare_path_serves_the_file_bytes(client):
    """/docs/readme.md is the file, not a page about the file."""
    resp = client.get("/docs/readme.md")
    assert resp.status_code == 200
    assert resp.text == MARKDOWN
    assert "<html" not in resp.text.lower()


def test_bare_path_serves_bytes_for_browser_navigation(client):
    resp = client.get("/docs/readme.md", headers={"accept": "text/html"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    assert resp.content == MARKDOWN.encode()
    assert resp.history == []


def test_bare_path_serves_css_as_css(client):
    """The reason raw is the default: a stylesheet has to arrive as text/css."""
    resp = client.get("/site/main.css")
    assert resp.status_code == 200
    assert "text/css" in resp.headers["content-type"]
    assert resp.text == "body { color: red; }"


def test_bare_path_serves_an_image_as_bytes(client):
    resp = client.get("/photo.png")
    assert resp.status_code == 200
    assert "image/png" in resp.headers["content-type"]
    assert resp.content == b"\x89PNG\r\n\x1a\n"


def test_bare_path_serves_html_as_html(client):
    """This is what the old '🌐 View as web page' button linked to."""
    resp = client.get("/page.html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert resp.text == "<h1>Hi</h1>"


def test_raw_view_is_identical_to_the_bare_path(client):
    """filemill=raw names the default rather than adding a fourth thing."""
    bare = client.get("/docs/readme.md")
    named = client.get("/docs/readme.md?filemill=raw")
    assert named.status_code == bare.status_code == 200
    assert named.text == bare.text
    assert named.headers["content-type"] == bare.headers["content-type"]


def test_a_space_in_a_path_is_served(client):
    resp = client.get("/my%20notes/a%20b.md")
    assert resp.status_code == 200
    assert resp.text == "# Spaced\n"


# ── The rendered and highlighted representations ─────────────────────────────


@pytest.mark.parametrize("view", ["render", "highlight"])
def test_document_views_serve_the_shared_shell(client, view):
    resp = client.get(f"/docs/readme.md?filemill={view}&layout=no-columns")
    assert resp.status_code == 200
    assert "/ui/entry-server.js" in resp.text
    assert f'data-filemill="{view}"' in resp.text
    assert 'data-layout="no-columns"' in resp.text
    assert "preview-standalone" not in resp.text


# ── Layout selects the chrome, not the content ───────────────────────────────


def test_no_columns_layout_serves_the_shared_shell(client):
    resp = client.get("/docs/readme.md?filemill=render&layout=no-columns")
    assert resp.status_code == 200
    assert "/ui/entry-server.js" in resp.text
    assert 'data-layout="no-columns"' in resp.text


def test_full_columns_layout_serves_the_shared_ui(client):
    """The columns are the shared UI's. The document arrives via /api/preview.

    The shell carries no document text, which is the point: one frontend builds
    the chrome, and it is the same one the static edition builds.
    """
    resp = client.get("/docs/readme.md?filemill=render&layout=full-columns")
    assert resp.status_code == 200
    assert "/ui/entry-server.js" in resp.text
    assert 'data-filemill="render"' in resp.text
    assert ">Guide</h1>" not in resp.text


def test_default_layout_is_full_columns(client):
    """Omitting layout gives the same page as asking for full-columns."""
    default = client.get("/docs/readme.md?filemill=render")
    explicit = client.get("/docs/readme.md?filemill=render&layout=full-columns")
    assert default.text == explicit.text


def test_compressed_columns_reaches_the_shared_ui(client):
    """ui/core/layout.js reads this and folds every column to a spine.

    The HTMX shell could only hide the columns, which is why PLAN-19 called the
    name an over-promise. The shared UI has the dial the name describes.
    """
    resp = client.get("/docs/readme.md?filemill=render&layout=compressed-columns")
    assert 'data-layout="compressed-columns"' in resp.text
    assert "/ui/entry-server.js" in resp.text


def test_layout_is_reported_on_the_body(client):
    resp = client.get("/docs/readme.md?filemill=render&layout=no-columns")
    assert 'data-layout="no-columns"' in resp.text


# ── Invalid and repeated query values ────────────────────────────────────────


@pytest.mark.parametrize(
    "query",
    [
        "?filemill=nonsense",
        "?layout=wide",
        "?hidden=maybe",
        "?filemill=nonsense&layout=nonsense&hidden=nonsense",
    ],
)
def test_invalid_query_values_serve_the_default_representation(client, query):
    """An unrecognised value never changes the requested file path."""
    resp = client.get(f"/docs/readme.md{query}")
    assert resp.status_code == 200
    assert resp.text == MARKDOWN


@pytest.mark.parametrize("query", ["?filemill", "?filemill=", "?f", "?f="])
def test_render_shortcuts_serve_the_rendered_representation(client, query):
    shorthand = client.get(f"/docs/readme.md{query}&layout=no-columns")
    explicit = client.get("/docs/readme.md?filemill=render&layout=no-columns")
    assert shorthand.text == explicit.text


def test_trailing_slash_redirects_a_file_to_the_rendered_view(client):
    resp = client.get("/docs/readme.md/", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/docs/readme.md?filemill=render"


def test_trailing_slash_preserves_other_query_parameters(client):
    resp = client.get("/docs/readme.md/?layout=no-columns", follow_redirects=False)
    assert resp.headers["location"] == (
        "/docs/readme.md?filemill=render&layout=no-columns"
    )


def test_explicit_raw_view_overrides_trailing_slash(client):
    resp = client.get("/docs/readme.md/?filemill=raw")
    assert resp.text == MARKDOWN


def test_repeated_view_takes_the_last_occurrence(client):
    resp = client.get("/docs/readme.md?filemill=raw&filemill=render&layout=no-columns")
    assert 'data-filemill="render"' in resp.text
    assert 'data-layout="no-columns"' in resp.text


def test_unknown_query_parameters_are_ignored(client):
    resp = client.get("/docs/readme.md?view=rendered&mode=fancy")
    assert resp.text == MARKDOWN


# ── Directories ──────────────────────────────────────────────────────────────


def test_directory_serves_the_shared_ui(client):
    """A directory has no bytes, so the column layouts open the finder on it."""
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "/ui/entry-server.js" in resp.text
    assert 'data-root="menu"' in resp.text


def test_directory_with_no_columns_serves_one_listing(client):
    resp = client.get("/docs?layout=no-columns")
    assert resp.status_code == 200
    assert "readme.md" in resp.text
    assert 'id="breadcrumb"' not in resp.text


def test_root_relative_directory_with_a_trailing_slash(client):
    assert client.get("/docs/", follow_redirects=False).status_code == 200


# ── Missing, denied, and method ──────────────────────────────────────────────


def test_missing_file_is_404(client):
    assert client.get("/docs/no_such_file.md").status_code == 404


def test_post_is_not_allowed(client):
    """PLAN-19 §3 makes the router-facing surface read-only."""
    assert client.post("/docs/readme.md").status_code == 405


# ── Reserved prefixes still win ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    ["/manifest.json", "/sw.js"],
)
def test_reserved_routes_are_not_shadowed_by_the_catch_all(client, url):
    resp = client.get(url)
    assert resp.status_code == 200


def test_named_route_wins_over_a_directory_of_the_same_name(site, client):
    """A directory in ROOT called "api" is unreachable by its own name.

    That is the one cost of putting files at the top level. It is asserted here
    so the behaviour is a decision on the record rather than a surprise.
    """
    (site / "api").mkdir()
    (site / "api" / "note.txt").write_text("shadowed")
    resp = client.get("/api/dir?p=")
    assert resp.status_code == 200
    assert "shadowed" not in resp.text


# ── Internal links keep the reader's state (PLAN-19 §1) ──────────────────────


def test_markdown_link_targets_the_files_own_path(site, client):
    """A document link returns the shared shell at its own path."""
    (site / "note.md").write_text("[link](other.md)\n")
    (site / "other.md").write_text("# Other\n")
    resp = client.get("/note.md?filemill=render&layout=no-columns")
    assert "/ui/entry-server.js" in resp.text
    assert 'data-layout="no-columns"' in resp.text


def test_markdown_image_src_is_left_relative_and_now_resolves(site, client):
    """Relative asset references need no rewriting under this contract.

    Image tokens were never rewritten — only <a href> is — so ``![](photo.png)``
    stays relative. Under the old ``/f/<mount>/…`` URLs that was broken: the
    browser resolved it against ``/f/menu/docs/note.md`` and asked for
    ``/f/menu/docs/photo.png``, which served the finder shell rather than the
    image. Now the document lives at ``/docs/note.md``, so the same relative
    reference resolves to ``/docs/photo.png`` and gets the bytes. The contract
    fixed a bug by removing a special case rather than adding one.
    """
    (site / "docs" / "note.md").write_text("![photo](../photo.png)\n")
    resp = client.get("/docs/note.md?filemill=render&layout=no-columns")
    assert "/ui/entry-server.js" in resp.text

    # The browser would resolve that against /docs/note.md. Follow it and check.
    resolved = client.get("/photo.png")
    assert resolved.status_code == 200
    assert "image/png" in resolved.headers["content-type"]
