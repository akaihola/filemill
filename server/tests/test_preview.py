import html as html_lib

import pytest

import filemill.preview as preview_module
from filemill.preview import (
    _preview_desktop,
    _preview_html,
    _preview_image,
    _preview_pdf,
    render_preview,
    render_source,
)

# ── render_preview dispatch ───────────────────────────────────────────────────


def test_dispatch_desktop(tmp_path):
    f = tmp_path / "link.desktop"
    f.write_text("[Desktop Entry]\nType=Link\nURL=https://ex.com\nName=Ex\n")
    assert "preview-desktop-link" in render_preview(f)


def test_dispatch_md_falls_through_to_coloured_source(tmp_path):
    """The browser renders Markdown; the server only ever shows its source."""
    f = tmp_path / "note.md"
    f.write_text("# Hi\n**bold**\n")
    html = render_preview(f)
    assert "preview-code" in html
    assert "<strong>" not in html


def test_dispatch_rst(tmp_path):
    f = tmp_path / "note.rst"
    f.write_text("Heading\n=======\n\nSome *rst* text.\n")
    html = render_preview(f)
    assert "<h1" in html
    assert "Some <em>rst</em> text." in html


def test_rst_links_keep_only_safe_urls(tmp_path):
    """docutils writes a link target as the document gives it (A2)."""
    f = tmp_path / "note.rst"
    f.write_text(
        "`run <javascript:alert(1)>`_ `page <data:text/html,x>`_ "
        "`web <https://example.com/>`_ `mail <mailto:a@example.com>`_ "
        "`sib <sib.rst>`_\n"
    )
    html = render_preview(f)
    assert "javascript:" not in html and "data:text" not in html, html
    assert ">run</a>" in html and ">page</a>" in html, html
    assert 'href="https://example.com/"' in html, html
    assert 'href="mailto:' in html and 'href="sib.rst"' in html, html


def test_source_rst_is_syntax_highlighted(tmp_path):
    f = tmp_path / "note.rst"
    f.write_text("Heading\n=======\n\n.. code-block:: python\n\n   return 1\n")
    html = render_source(f)
    assert "preview-code" in html


def test_unknown_extension_utf8_is_plain_text(tmp_path):
    f = tmp_path / ".gitconfig"
    f.write_text("[user]\nname = Åsa\n")
    assert "preview-" in render_preview(f)


def test_binary_and_insanely_wide_text_are_unsupported(tmp_path):
    binary = tmp_path / "notes"
    binary.write_bytes(b"ok\0bad")
    wide = tmp_path / "wide"
    wide.write_text("x" * 10_001)
    assert "preview-unsupported" in render_preview(binary)
    assert "preview-raw" in render_preview(wide)


def test_dispatch_docx_is_unsupported_on_the_server(tmp_path):
    """The browser renders .docx with mammoth; the server has no renderer."""
    f = tmp_path / "doc.docx"
    f.write_bytes(b"PK\x03\x04\x00fake")
    assert "preview-unsupported" in render_preview(f)


def test_dispatch_pdf(tmp_path):
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF")
    assert "preview-pdf" in render_preview(f)


@pytest.mark.parametrize("ext", [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"])
def test_dispatch_image(tmp_path, ext):
    f = tmp_path / f"img{ext}"
    f.write_bytes(b"fake")
    assert "preview-image" in render_preview(f)


def test_dispatch_unknown_ext(tmp_path):
    """Binary file with unknown extension → preview-unsupported with extension name."""
    f = tmp_path / "data.xyz"
    f.write_bytes(b"\x00\x01\x02\xff\xfe")  # binary; UTF-8 decode fails
    result = render_preview(f)
    assert "preview-unsupported" in result
    assert ".xyz" in result


def test_dispatch_no_ext(tmp_path):
    """Binary file with no extension → '(no extension)' in unsupported message."""
    f = tmp_path / "noext"
    f.write_bytes(b"\x00\x01\x02\xff\xfe")  # binary; UTF-8 decode fails
    result = render_preview(f)
    assert "preview-unsupported" in result
    assert "(no extension)" in result


# ── _preview_pdf ──────────────────────────────────────────────────────────────


def test_preview_pdf_contains_iframe(tmp_path):
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF")
    html = _preview_pdf(f)
    assert "preview-pdf" in html
    assert "<iframe" in html
    assert "/api/raw?p=doc.pdf" in html


def test_preview_pdf_uses_the_relative_url_when_provided(tmp_path):
    html = _preview_pdf(tmp_path / "doc.pdf", "/api/raw?p=docs%2Fdoc.pdf")
    assert 'src="/api/raw?p=docs%2Fdoc.pdf"' in html


# ── _preview_html ─────────────────────────────────────────────────────────────


def test_dispatch_html(tmp_path):
    f = tmp_path / "page.html"
    f.write_text("<h1>Hi</h1>")
    assert "preview-html" in render_preview(f)


def test_preview_html_contains_iframe(tmp_path):
    f = tmp_path / "page.htm"
    f.write_text("<h1>Hi</h1>")
    html = _preview_html(f)
    assert "preview-html" in html
    assert "<iframe" in html
    assert 'src="/api/raw?p=page.htm"' in html


def test_source_view_html_stays_source(tmp_path):
    """?filemill=highlight must keep showing the markup, not an <iframe>."""
    f = tmp_path / "page.html"
    f.write_text("<h1>Hi</h1>")
    assert "<iframe" not in render_source(f)


# ── _preview_image ────────────────────────────────────────────────────────────


def test_preview_image_contains_img_tag(tmp_path):
    f = tmp_path / "img.png"
    f.write_bytes(b"\x89PNG")
    html = _preview_image(f)
    assert "preview-image" in html
    assert '<img class="pv-img"' in html
    assert "/api/raw?p=img.png" in html


def test_preview_image_uses_the_relative_url_when_provided(tmp_path):
    html = _preview_image(tmp_path / "img.png", "/api/raw?p=images%2Fimg.png")
    assert 'src="/api/raw?p=images%2Fimg.png"' in html


def test_preview_image_alt_is_filename(tmp_path):
    f = tmp_path / "photo.jpg"
    f.write_bytes(b"JFIF")
    assert 'alt="photo.jpg"' in _preview_image(f)


# ── _preview_desktop ──────────────────────────────────────────────────────────


def test_preview_desktop_valid_link(tmp_path):
    f = tmp_path / "link.desktop"
    f.write_text("[Desktop Entry]\nType=Link\nURL=https://example.com\nName=Example\n")
    html = _preview_desktop(f)
    assert "preview-desktop-link" in html
    assert "https://example.com" in html


def test_preview_desktop_http_icon_rendered(tmp_path):
    f = tmp_path / "link.desktop"
    f.write_text(
        "[Desktop Entry]\nType=Link\nURL=https://ex.com\nName=Ex\n"
        "Icon=https://ex.com/icon.png\n"
    )
    assert '<img src="https://ex.com/icon.png"' in _preview_desktop(f)


def test_preview_desktop_local_icon_not_rendered(tmp_path):
    """Non-http icon names must NOT produce an <img> element."""
    f = tmp_path / "link.desktop"
    f.write_text(
        "[Desktop Entry]\nType=Link\nURL=https://ex.com\nName=Ex\n"
        "Icon=application-icon\n"
    )
    assert 'src="application-icon"' not in _preview_desktop(f)


def test_preview_desktop_with_comment(tmp_path):
    f = tmp_path / "link.desktop"
    f.write_text(
        "[Desktop Entry]\nType=Link\nURL=https://ex.com\nName=Ex\nComment=My note\n"
    )
    assert "My note" in _preview_desktop(f)


def test_preview_desktop_no_comment_no_paragraph(tmp_path):
    """Absent Comment key must not produce the grey comment <p>."""
    f = tmp_path / "link.desktop"
    f.write_text("[Desktop Entry]\nType=Link\nURL=https://ex.com\nName=Ex\n")
    assert "color:#aaa" not in _preview_desktop(f)


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "JavaScript:alert(1)",
        "java\tscript:alert(1)",
        "data:text/html,<b>x</b>",
        "vbscript:msgbox(1)",
    ],
)
def test_preview_desktop_unsafe_url_is_text(tmp_path, url):
    """Only a safe protocol becomes a link; the rest is shown, not followed."""
    f = tmp_path / "link.desktop"
    f.write_text(f"[Desktop Entry]\nType=Link\nURL={url}\nName=Ex\n")
    html = _preview_desktop(f)
    assert "href" not in html, html
    assert html_lib.escape(url) in html, html


def test_preview_desktop_non_link_type(tmp_path):
    f = tmp_path / "app.desktop"
    f.write_text("[Desktop Entry]\nType=Application\nName=App\n")
    html = _preview_desktop(f)
    assert "preview-unsupported" in html
    assert "no URL to open" in html


def test_preview_desktop_link_type_empty_url(tmp_path):
    """Type=Link but no URL key → 'no URL to open' message."""
    f = tmp_path / "link.desktop"
    f.write_text("[Desktop Entry]\nType=Link\nName=NoURL\n")
    html = _preview_desktop(f)
    assert "preview-unsupported" in html
    assert "no URL to open" in html


def test_preview_desktop_no_section(tmp_path):
    """File without [Desktop Entry] section → 'Not a valid .desktop file'."""
    f = tmp_path / "bad.desktop"
    f.write_text("[OtherSection]\nFoo=Bar\n")
    assert "Not a valid .desktop file" in _preview_desktop(f)


def test_preview_desktop_exception(tmp_path, monkeypatch):
    """ConfigParser.read raises → preview-error div."""
    f = tmp_path / "link.desktop"
    f.write_text("irrelevant")
    import configparser as cp_mod

    def boom(self, *a, **kw):
        raise RuntimeError("parse failure")

    monkeypatch.setattr(cp_mod.ConfigParser, "read", boom)
    assert "preview-error" in _preview_desktop(f)


# ── #7 raw UTF-8 text fallback ────────────────────────────────────────────────


def test_raw_utf8_text_file_shows_preview_raw(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("hello world\nline 2\n")
    result = render_preview(f)
    assert "preview-raw" in result
    assert "hello world" in result


def test_binary_file_shows_unsupported(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02\xff\xfe")
    result = render_preview(f)
    assert "No preview available" in result


def test_large_text_file_shows_unsupported(tmp_path):
    # File must exceed BOTH the Pygments limit (512 KB) AND the raw-text limit
    # (256 KB) so that render_preview() falls all the way through to "No
    # preview available" without calling guess_lexer() on a huge blob of
    # repeated bytes (which hangs indefinitely – see issue #17).
    f = tmp_path / "big.log"
    f.write_bytes(b"x" * (512 * 1024 + 1))
    result = render_preview(f)
    assert "No preview available" in result


def test_raw_text_html_escaped(tmp_path):
    f = tmp_path / "code.txt"
    f.write_text("<script>alert('xss')</script>\n")
    result = render_preview(f)
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


# ── #14 syntax highlighting ───────────────────────────────────────────────────


def test_python_file_is_syntax_highlighted(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text("def hello():\n    return 'world'\n")
    result = render_preview(f)
    assert "preview-code" in result
    assert "highlight" in result  # Pygments wraps in div.highlight


def test_jinja_python_file_is_syntax_highlighted(tmp_path):
    f = tmp_path / "hello.py.j2"
    f.write_text("def hello():\n    return 'world'\n")
    result = render_preview(f)
    assert "preview-code" in result


def test_js_file_is_syntax_highlighted(tmp_path):
    f = tmp_path / "app.js"
    f.write_text("function hello() { return 'world'; }\n")
    result = render_preview(f)
    assert "preview-code" in result


def test_large_code_file_falls_through(tmp_path):
    """Files over 512 KB must not be syntax-highlighted (fallback to raw or unsupported)."""
    f = tmp_path / "big.py"
    f.write_bytes(b"# comment\n" * 52429)  # >512 KB
    result = render_preview(f)
    # Must NOT have preview-code (too large for highlighting)
    assert "preview-code" not in result


def test_binary_py_file_falls_through(tmp_path):
    """A .py file with non-UTF8 bytes must not crash – fall through to next handler."""
    f = tmp_path / "bytes.py"
    f.write_bytes(b"\xff\xfe invalid utf-8")
    result = render_preview(f)  # must not raise
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
    result = render_preview(f)
    assert "preview-raw" in result


def test_preview_pygments_outer_exception_falls_through(tmp_path, monkeypatch):
    """An exception from pyg_highlight() must be caught; file falls through to raw-text."""

    def _raise(*_a, **_kw):
        raise RuntimeError("highlight broken")

    monkeypatch.setattr(preview_module, "pyg_highlight", _raise)
    f = tmp_path / "script.py"
    f.write_text("x = 1\n")
    result = render_preview(f)
    # highlight raised → fell through to raw-text preview
    assert "preview-code" not in result
    assert "preview-raw" in result
