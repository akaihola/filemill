import re
from html.parser import HTMLParser
from pathlib import Path
from textwrap import dedent

import pytest

import filemill.preview as preview_module
from filemill.preview import render_rst, render_source


def rst_html(path: Path) -> str:
    """reStructuredText is the one kind the server renders ([162])."""
    return render_rst(path.read_bytes())


# ── render_rst ────────────────────────────────────────────────────────────────


def test_render_rst(tmp_path):
    f = tmp_path / "note.rst"
    f.write_text("Heading\n=======\n\nSome *rst* text.\n")
    html = rst_html(f)
    assert "<h1" in html
    assert "Some <em>rst</em> text." in html


def test_render_rst_renders_a_line_range():
    source = b"Title\n=====\n\nPart A\n------\n\nalpha\n\nPart B\n------\n\nbeta\n"
    html = render_rst(source, (8, 12))
    assert "Part B" in html and "beta" in html
    assert "alpha" not in html and "Part A" not in html


def test_render_rst_reports_undecodable_bytes():
    assert "preview-error" in render_rst(b"\xff\xfe not utf-8")


def test_rst_links_keep_only_safe_urls(tmp_path):
    """docutils writes a link target as the document gives it (A2)."""
    f = tmp_path / "note.rst"
    f.write_text(
        "`run <javascript:alert(1)>`_ `page <data:text/html,x>`_ "
        "`web <https://example.com/>`_ `mail <mailto:a@example.com>`_ "
        "`sib <sib.rst>`_\n"
    )
    html = rst_html(f)
    assert "javascript:" not in html and "data:text" not in html, html
    assert ">run</a>" in html and ">page</a>" in html, html
    assert 'href="https://example.com/"' in html, html
    assert 'href="mailto:' in html and 'href="sib.rst"' in html, html


class _Markup(HTMLParser):
    """Every element and attribute in a fragment, as a browser's parser finds
    them."""

    def __init__(self):
        super().__init__()
        self.elements: list[tuple[str, list[tuple[str, str | None]]]] = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, attrs))


def _elements(html: str) -> list[tuple[str, list[tuple[str, str | None]]]]:
    parser = _Markup()
    parser.feed(html)
    parser.close()
    return parser.elements


def _attribute_names(html: str) -> list[str]:
    return [name for _, attrs in _elements(html) for name, _ in attrs]


def _tag_names(html: str) -> set[str]:
    return {tag for tag, _ in _elements(html)}


def _live(names: list[str]) -> list[str]:
    return [n for n in names if n.startswith("on") or n in ("data", "xlink:href")]


@pytest.fixture()
def outside(tmp_path):
    """A served root and, beside it, files the root does not contain (S2)."""
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "secret.png").write_bytes(b"\x89PNG secret pixels")
    (outside / "evil.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" onload="window.__xss=1">'
        '<circle r="5"/></svg>'
    )
    return outside


@pytest.mark.parametrize(
    "target",
    ["{outside}/secret.png", "file://{outside}/secret.png", "{outside}/evil.svg"],
)
def test_rst_never_inlines_an_image_file(tmp_path, outside, target):
    """docutils embeds an image for ``:loading: embed`` whatever
    file_insertion_enabled says, from any path the server can read (S2)."""
    f = tmp_path / "root" / "note.rst"
    f.write_text(f".. image:: {target.format(outside=outside)}\n   :loading: embed\n")
    html = rst_html(f)
    assert "data:" not in html and "c2VjcmV0" not in html, html
    assert "<svg" not in html and "onload" not in html, html
    assert "preview-error" not in html and "<img" in html, html


def test_rst_images_inside_the_root_stay_links(tmp_path, outside):
    root = tmp_path / "root"
    (root / "pics").mkdir()
    (root / "pics" / "cat.png").write_bytes(b"\x89PNG cat")
    f = root / "note.rst"
    f.write_text(
        '.. image:: pics/cat.png\n   :alt: A "cat" & dog\n\n'
        ".. image:: pics/cat.png\n   :loading: embed\n\n"
        ".. image:: pics/cat.png\n   :loading: lazy\n"
    )
    html = rst_html(f)
    assert '<img alt="A &quot;cat&quot; &amp; dog" src="pics/cat.png" />' in html
    assert html.count('src="pics/cat.png"') == 3 and "data:" not in html, html
    assert 'loading="lazy"' in html, html


@pytest.mark.parametrize(
    "source",
    [
        # docutils writes a video's address and alternative text into its
        # fallback link unescaped.
        '.. image:: x"onmouseover="window.__xss=1"x=".mp4\n',
        ".. image:: clip.mp4\n   :alt: <img src=x onerror=window.__xss=2>\n",
        ".. image:: {outside}/evil.svg\n   :loading: embed\n",
    ],
)
def test_rst_preview_keeps_no_event_handler(tmp_path, outside, source):
    f = tmp_path / "root" / "note.rst"
    f.write_text(source.format(outside=outside))
    html = rst_html(f)
    assert _live(_attribute_names(html)) == [], html


# Elements docutils never writes, which a document's text can still bring in.
FOREIGN = {
    "frame": "<iframe></iframe>",
    "embed": "<embed>",
    "form": "<form></form>",
    "base": "<base>",
    "svg-animation": "<svg><animate></animate></svg>",
}
FOREIGN_TAGS = {"iframe", "embed", "form", "base", "svg", "animate"}


@pytest.mark.parametrize("field", ["alt", "address"])
@pytest.mark.parametrize("markup", FOREIGN.values(), ids=FOREIGN.keys())
def test_rst_preview_keeps_only_elements_docutils_writes(tmp_path, field, markup):
    """docutils writes a video's address and alternative text into its
    fallback link unescaped, so markup in either reaches its output."""
    f = tmp_path / "note.rst"
    f.write_text(
        f".. image:: clip.mp4\n   :alt: {markup}\n"
        if field == "alt"
        else f".. image:: {markup}.mp4\n"
    )
    html = rst_html(f)
    assert FOREIGN_TAGS.isdisjoint(_tag_names(html)), html
    assert "<video" in html, html


ORDINARY_RST = dedent(
    """\
    Title
    =====

    Section
    -------

    Some *emphasis*, **strong**, ``literal``, :sub:`2`, :sup:`3`,
    :title-reference:`a book`, :math:`a^2 + b^2`, a
    `link <https://example.com/>`_, a footnote [#]_ and `Section`_.

    .. [#] A footnote.

    - one
    - two

    3. three
    4. four

    term
      definition

    :field: value

    | line one
    | line two

       A quotation.

       -- Someone

    +-----+-----+
    | A   | B   |
    +=====+=====+
    | spans both|
    +-----+-----+

    .. list-table:: Caption
       :header-rows: 1
       :widths: 30 70

       * - h1
         - h2
       * - a
         - b

    ::

       literal

    .. code-block:: python
       :number-lines:

       return 1

    .. image:: pics/cat.png
       :width: 50%
       :align: center
       :alt: cat

    .. figure:: pics/cat.png
       :figwidth: 60%

       A caption.

    .. image:: clip.mp4
       :class: controls

    .. note:: A note.

    .. admonition:: Custom

       Body.

    .. sidebar:: Aside

       Body.

    .. contents::

    .. math::

       \\frac{1}{2}
    """
)


def test_ordinary_rst_keeps_everything_docutils_writes(tmp_path, monkeypatch):
    """The check drops nothing from an ordinary document: headings, lists,
    tables, code, links, images, admonitions and math."""
    f = tmp_path / "note.rst"
    f.write_text(ORDINARY_RST)
    checked = rst_html(f)
    monkeypatch.setattr(preview_module, "_inert", lambda html: html)
    unchecked = rst_html(f)
    assert {"table", "pre", "img", "video", "aside", "math"} <= _tag_names(unchecked)
    assert _elements(checked) == _elements(unchecked)


def test_rst_allowlist_matches_the_browsers_copy():
    """ui/adapters/preview-rich.js checks reStructuredText the browser renders
    against the same lists."""
    script = (
        Path(preview_module.__file__).parent / "ui/adapters/preview-rich.js"
    ).read_text()
    found = re.search(
        r"RST_HTML = \{\s*tags:(.*?)\battrs:(.*?)\n\};", script, re.DOTALL
    )
    assert found, "RST_HTML not found in preview-rich.js"

    def words(js: str) -> set[str]:
        return set(" ".join(re.findall(r'"([^"]*)"', js)).split())

    assert words(found[1]) == preview_module.RST_TAGS
    assert words(found[2]) == preview_module.RST_ATTRIBUTES


def test_source_rst_is_syntax_highlighted(tmp_path):
    f = tmp_path / "note.rst"
    f.write_text("Heading\n=======\n\n.. code-block:: python\n\n   return 1\n")
    html = render_source(f)
    assert "preview-code" in html


# ── render_source ─────────────────────────────────────────────────────────────


def test_unknown_extension_utf8_is_plain_text(tmp_path):
    f = tmp_path / ".gitconfig"
    f.write_text("[user]\nname = Åsa\n")
    assert "preview-" in render_source(f)


def test_binary_and_insanely_wide_text_are_unsupported(tmp_path):
    binary = tmp_path / "notes"
    binary.write_bytes(b"ok\0bad")
    wide = tmp_path / "wide"
    wide.write_text("x" * 10_001)
    assert "preview-unsupported" in render_source(binary)
    assert "preview-raw" in render_source(wide)


def test_source_of_unknown_ext(tmp_path):
    """Binary file with unknown extension → preview-unsupported with extension name."""
    f = tmp_path / "data.xyz"
    f.write_bytes(b"\x00\x01\x02\xff\xfe")  # binary; UTF-8 decode fails
    result = render_source(f)
    assert "preview-unsupported" in result
    assert ".xyz" in result


def test_source_of_no_ext(tmp_path):
    """Binary file with no extension → '(no extension)' in unsupported message."""
    f = tmp_path / "noext"
    f.write_bytes(b"\x00\x01\x02\xff\xfe")  # binary; UTF-8 decode fails
    result = render_source(f)
    assert "preview-unsupported" in result
    assert "(no extension)" in result


def test_source_view_html_stays_source(tmp_path):
    """?filemill=highlight must keep showing the markup, not an <iframe>."""
    f = tmp_path / "page.html"
    f.write_text("<h1>Hi</h1>")
    assert "<iframe" not in render_source(f)


# ── #7 raw UTF-8 text fallback ────────────────────────────────────────────────


def test_raw_utf8_text_file_shows_preview_raw(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("hello world\nline 2\n")
    result = render_source(f)
    assert "preview-raw" in result
    assert "hello world" in result


def test_binary_file_shows_unsupported(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02\xff\xfe")
    result = render_source(f)
    assert "No source view available" in result


def test_large_text_file_shows_unsupported(tmp_path):
    # File must exceed BOTH the Pygments limit (512 KB) AND the raw-text limit
    # (256 KB) so that render_source() falls all the way through to "No
    # source view available" without calling guess_lexer() on a huge blob of
    # repeated bytes (which hangs indefinitely – see issue #17).
    f = tmp_path / "big.log"
    f.write_bytes(b"x" * (512 * 1024 + 1))
    result = render_source(f)
    assert "No source view available" in result


def test_raw_text_html_escaped(tmp_path):
    f = tmp_path / "code.txt"
    f.write_text("<script>alert('xss')</script>\n")
    result = render_source(f)
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


# ── #14 syntax highlighting ───────────────────────────────────────────────────


def test_python_file_is_syntax_highlighted(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text("def hello():\n    return 'world'\n")
    result = render_source(f)
    assert "preview-code" in result
    assert "highlight" in result  # Pygments wraps in div.highlight


def test_jinja_python_file_is_syntax_highlighted(tmp_path):
    f = tmp_path / "hello.py.j2"
    f.write_text("def hello():\n    return 'world'\n")
    result = render_source(f)
    assert "preview-code" in result


def test_js_file_is_syntax_highlighted(tmp_path):
    f = tmp_path / "app.js"
    f.write_text("function hello() { return 'world'; }\n")
    result = render_source(f)
    assert "preview-code" in result


def test_large_code_file_falls_through(tmp_path):
    """Files over 512 KB must not be syntax-highlighted (fallback to raw or unsupported)."""
    f = tmp_path / "big.py"
    f.write_bytes(b"# comment\n" * 52429)  # >512 KB
    result = render_source(f)
    # Must NOT have preview-code (too large for highlighting)
    assert "preview-code" not in result


def test_binary_py_file_falls_through(tmp_path):
    """A .py file with non-UTF8 bytes must not crash – fall through to next handler."""
    f = tmp_path / "bytes.py"
    f.write_bytes(b"\xff\xfe invalid utf-8")
    result = render_source(f)  # must not raise
    assert "preview-code" not in result


def test_preview_guess_lexer_exception_falls_through(tmp_path, monkeypatch):
    """guess_lexer() raising must be caught; file must fall through to raw-text preview."""
    import pygments.lexers

    def _raise(*_a, **_kw):
        raise RuntimeError("lexer detection broken")

    monkeypatch.setattr(pygments.lexers, "guess_lexer", _raise)
    # Use an extension unknown to Pygments so get_lexer_by_name raises ClassNotFound
    # and guess_lexer is attempted (and patched to raise).
    f = tmp_path / "weirdfile.xyzzy1234"
    f.write_text("some content\n")
    result = render_source(f)
    assert "preview-raw" in result


def test_preview_pygments_outer_exception_falls_through(tmp_path, monkeypatch):
    """An exception from pyg_highlight() must be caught; file falls through to raw-text."""

    def _raise(*_a, **_kw):
        raise RuntimeError("highlight broken")

    monkeypatch.setattr(preview_module, "pyg_highlight", _raise)
    f = tmp_path / "script.py"
    f.write_text("x = 1\n")
    result = render_source(f)
    # highlight raised → fell through to raw-text preview
    assert "preview-code" not in result
    assert "preview-raw" in result
