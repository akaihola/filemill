"""One path, every representation (PLAN-19 §1–§5).

For a configured root containing ``docs/readme.md``, these are the addresses:

    /docs/readme.md                              the file's bytes
    /docs/readme.md?pykofinder-view=rendered     Markdown as HTML
    /docs/readme.md?pykofinder-view=highlighted  the source, coloured
    /docs/readme.md?pykofinder-view=raw          the bytes, said out loud

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
    """pykofinder-view=raw names the default rather than adding a fourth thing."""
    bare = client.get("/docs/readme.md")
    named = client.get("/docs/readme.md?pykofinder-view=raw")
    assert named.status_code == bare.status_code == 200
    assert named.text == bare.text
    assert named.headers["content-type"] == bare.headers["content-type"]


def test_a_space_in_a_path_is_served(client):
    resp = client.get("/my%20notes/a%20b.md")
    assert resp.status_code == 200
    assert resp.text == "# Spaced\n"


# ── The rendered and highlighted representations ─────────────────────────────


def test_rendered_view_renders_markdown(client):
    resp = client.get("/docs/readme.md?pykofinder-view=rendered")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert ">Guide</h1>" in resp.text
    assert "<em>emphasis</em>" in resp.text
    assert 'class="preview-md"' in resp.text


def test_rendered_view_passes_raw_html_through_unescaped(client):
    """Pinning pre-existing behaviour, because this change makes it matter more.

    ``MarkdownIt("commonmark")`` sets ``html: True``, so a <script> written into
    a Markdown file reaches the browser. That predates PLAN-19 and no test
    covered it. It is recorded here rather than changed quietly, because a
    rendered page is now served same-origin with the dashboard that embeds it,
    which raises the stakes of the existing choice. See PLAN-19 "What remains".
    """
    resp = client.get("/docs/readme.md?pykofinder-view=rendered")
    assert "<script>alert(1)</script>" in resp.text


def test_highlighted_view_shows_the_source_not_the_rendering(client):
    """The characters the author typed, coloured but not obeyed."""
    resp = client.get("/docs/readme.md?pykofinder-view=highlighted")
    assert resp.status_code == 200
    assert ">Guide</h1>" not in resp.text
    assert "# Guide" in resp.text
    assert 'class="preview-code"' in resp.text


def test_highlighted_view_escapes_markup_in_the_source(client):
    """The same <script> that runs in the rendered view is inert here."""
    resp = client.get("/docs/readme.md?pykofinder-view=highlighted")
    assert "<script>alert(1)</script>" not in resp.text
    assert "&lt;" in resp.text and "script" in resp.text


def test_highlighted_view_colours_source_code(client):
    resp = client.get("/hello.py?pykofinder-view=highlighted")
    assert resp.status_code == 200
    assert 'class="preview-code"' in resp.text
    assert "hello" in resp.text


def test_highlighted_view_of_html_shows_the_markup_not_the_page(client):
    """Pygments splits the tag across spans, so the angle brackets arrive escaped."""
    resp = client.get("/page.html?pykofinder-view=highlighted")
    assert resp.status_code == 200
    assert 'class="preview-code"' in resp.text
    assert "&lt;" in resp.text
    assert "<h1>Hi</h1>" not in resp.text


# ── Layout selects the chrome, not the content ───────────────────────────────


def test_no_columns_layout_omits_the_column_rail(client):
    resp = client.get("/docs/readme.md?pykofinder-view=rendered&layout=no-columns")
    assert resp.status_code == 200
    assert 'class="column"' not in resp.text
    assert 'id="breadcrumb"' not in resp.text
    assert ">Guide</h1>" in resp.text


def test_full_columns_layout_carries_the_column_rail(client):
    resp = client.get("/docs/readme.md?pykofinder-view=rendered&layout=full-columns")
    assert resp.status_code == 200
    assert 'class="column"' in resp.text
    assert 'id="breadcrumb"' in resp.text
    assert ">Guide</h1>" in resp.text


def test_default_layout_is_full_columns(client):
    """Omitting layout gives the same page as asking for full-columns."""
    default = client.get("/docs/readme.md?pykofinder-view=rendered")
    explicit = client.get(
        "/docs/readme.md?pykofinder-view=rendered&layout=full-columns"
    )
    assert default.text == explicit.text


def test_compressed_columns_sets_the_zoomed_presentation(client):
    """compressed-columns reuses the class the ⛶ button already toggles."""
    resp = client.get(
        "/docs/readme.md?pykofinder-view=rendered&layout=compressed-columns"
    )
    assert 'data-layout="compressed-columns"' in resp.text
    assert "zoomed" in resp.text


def test_layout_is_reported_on_the_body(client):
    resp = client.get("/docs/readme.md?pykofinder-view=rendered&layout=no-columns")
    assert 'data-layout="no-columns"' in resp.text


def test_hidden_show_reaches_the_body(client):
    resp = client.get("/docs/readme.md?pykofinder-view=rendered&hidden=show")
    assert 'data-hidden="show"' in resp.text
    assert "show-dotfiles" in resp.text


def test_hidden_defaults_to_hide(client):
    resp = client.get("/docs/readme.md?pykofinder-view=rendered")
    assert 'data-hidden="hide"' in resp.text


# ── The switch controls are reciprocal and query-preserving ──────────────────


def test_rendered_view_links_to_the_other_two(client):
    resp = client.get("/docs/readme.md?pykofinder-view=rendered&layout=no-columns")
    assert (
        'data-pykofinder-view="highlighted"'
        ' href="/docs/readme.md?pykofinder-view=highlighted&amp;layout=no-columns"'
    ) in resp.text
    assert 'data-pykofinder-view="raw" href="/docs/readme.md?layout=no-columns"' in (
        resp.text
    )


def test_highlighted_view_links_back_to_rendered(client):
    """The reciprocal half of the pair, asserted as an exact href."""
    resp = client.get("/docs/readme.md?pykofinder-view=highlighted&layout=no-columns")
    assert (
        'data-pykofinder-view="rendered"'
        ' href="/docs/readme.md?pykofinder-view=rendered&amp;layout=no-columns"'
    ) in resp.text


def test_switch_links_preserve_hidden(client):
    resp = client.get(
        "/docs/readme.md?pykofinder-view=rendered&layout=no-columns&hidden=show"
    )
    assert (
        'href="/docs/readme.md?pykofinder-view=highlighted'
        '&amp;layout=no-columns&amp;hidden=show"' in resp.text
    )


def test_switch_link_to_raw_is_the_bare_path_when_nothing_else_is_set(client):
    """Clicking Raw lands on the canonical short URL, which teaches the contract."""
    resp = client.get("/docs/readme.md?pykofinder-view=rendered")
    assert 'data-pykofinder-view="raw" href="/docs/readme.md"' in resp.text


def test_the_active_view_is_marked(client):
    resp = client.get("/docs/readme.md?pykofinder-view=rendered")
    assert 'data-pykofinder-view="rendered" href=' in resp.text
    assert 'aria-current="page"' in resp.text


def test_the_switch_has_a_stable_class(client):
    resp = client.get("/docs/readme.md?pykofinder-view=rendered")
    assert "pykofinder-view-switch" in resp.text


# ── Invalid and repeated query values ────────────────────────────────────────


@pytest.mark.parametrize(
    "query",
    [
        "?pykofinder-view=nonsense",
        "?pykofinder-view=",
        "?layout=wide",
        "?hidden=maybe",
        "?pykofinder-view=nonsense&layout=nonsense&hidden=nonsense",
    ],
)
def test_invalid_query_values_serve_the_default_representation(client, query):
    """An unrecognised value never changes the requested file path."""
    resp = client.get(f"/docs/readme.md{query}")
    assert resp.status_code == 200
    assert resp.text == MARKDOWN


def test_repeated_view_takes_the_last_occurrence(client):
    resp = client.get(
        "/docs/readme.md?pykofinder-view=raw&pykofinder-view=rendered&layout=no-columns"
    )
    assert ">Guide</h1>" in resp.text


def test_unknown_query_parameters_are_ignored(client):
    resp = client.get("/docs/readme.md?view=rendered&mode=fancy")
    assert resp.text == MARKDOWN


# ── Directories ──────────────────────────────────────────────────────────────


def test_directory_serves_the_column_layout(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert 'class="column"' in resp.text
    assert "readme.md" in resp.text


def test_directory_with_no_columns_serves_one_listing(client):
    resp = client.get("/docs?layout=no-columns")
    assert resp.status_code == 200
    assert "readme.md" in resp.text
    assert 'id="breadcrumb"' not in resp.text


def test_root_relative_directory_with_a_trailing_slash(client):
    assert client.get("/docs/").status_code == 200


# ── Missing, denied, and method ──────────────────────────────────────────────


def test_missing_file_is_404(client):
    assert client.get("/docs/no_such_file.md").status_code == 404


def test_post_is_not_allowed(client):
    """PLAN-19 §3 makes the router-facing surface read-only."""
    assert client.post("/docs/readme.md").status_code == 405


# ── Reserved prefixes still win ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    ["/f/", "/manifest.json", "/sw.js"],
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


def test_click_route_still_answers_its_own_path(client, site):
    from urllib.parse import quote

    target = site / "docs" / "readme.md"
    resp = client.get(f"/click?path={quote(str(target))}&col=1")
    assert resp.status_code == 200
    assert "preview-md" in resp.text


# ── Internal links keep the reader's state (PLAN-19 §1) ──────────────────────


def test_markdown_link_targets_the_files_own_path(site, client):
    """A [link](other.md) resolves to /other.md?pykofinder-view=rendered."""
    (site / "note.md").write_text("[link](other.md)\n")
    (site / "other.md").write_text("# Other\n")
    resp = client.get("/note.md?pykofinder-view=rendered")
    assert 'href="/other.md?pykofinder-view=rendered"' in resp.text


def test_markdown_link_keeps_a_no_columns_reader_in_no_columns(site, client):
    """Following a link inside an embedded document must not open the finder."""
    (site / "note.md").write_text("[link](other.md)\n")
    (site / "other.md").write_text("# Other\n")
    resp = client.get("/note.md?pykofinder-view=rendered&layout=no-columns")
    assert (
        'href="/other.md?pykofinder-view=rendered&amp;layout=no-columns"' in resp.text
    )


def test_markdown_link_keeps_hidden(site, client):
    (site / "note.md").write_text("[link](other.md)\n")
    (site / "other.md").write_text("# Other\n")
    resp = client.get("/note.md?pykofinder-view=rendered&hidden=show")
    assert 'href="/other.md?pykofinder-view=rendered&amp;hidden=show"' in resp.text


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
    resp = client.get("/docs/note.md?pykofinder-view=rendered")
    assert 'src="../photo.png"' in resp.text

    # The browser would resolve that against /docs/note.md. Follow it and check.
    resolved = client.get("/photo.png")
    assert resolved.status_code == 200
    assert "image/png" in resolved.headers["content-type"]


def test_click_fragment_links_do_not_gain_a_layout(site, client):
    """/click has no ViewState, so its links carry the documented defaults."""
    from urllib.parse import quote

    (site / "note.md").write_text("[link](other.md)\n")
    (site / "other.md").write_text("# Other\n")
    resp = client.get(f"/click?path={quote(str(site / 'note.md'))}&col=1")
    assert 'href="/other.md?pykofinder-view=rendered"' in resp.text
