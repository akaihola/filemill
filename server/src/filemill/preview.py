import configparser
import html as html_lib
import re
from contextlib import suppress
from pathlib import Path
from urllib.parse import quote as urlquote

from docutils.core import publish_parts
from pygments import highlight as pyg_highlight
from pygments.formatters import HtmlFormatter as PygHtmlFormatter
from pygments.lexers import (
    ClassNotFound,
    TextLexer,
    get_lexer_by_name,
    guess_lexer,
)

from filemill.vfs import classify_path

# Largest file Pygments is asked to colour, and largest one shown as plain <pre>.
SYNTAX_SIZE_LIMIT = 512 * 1024  # 512 KB
RAW_SIZE_LIMIT = SYNTAX_SIZE_LIMIT
MAX_LINE_LENGTH = 10_000

# The protocols a preview may link to (A2); a scheme-less address resolves
# against the page, so it may stay too. Browsers drop tabs, newlines and leading
# controls before they read a scheme, so the literal value is tested: one that
# does not start with a listed protocol must have no colon before its first
# slash, query or fragment. ui/core/model/safe-url.js is the browser's copy.
SAFE_PROTOCOLS = ("http:", "https:", "mailto:")
_SCHEME_LIKE = re.compile(r"[^/?#]*:")

# docutils escapes and double-quotes every attribute value, and with raw input
# off nothing else writes markup into its output, so a quoted href or src there
# is always one of its own.
_URL_ATTR = re.compile(r' (href|src)="([^"]*)"')


def safe_url(url: str) -> bool:
    """Whether *url* may be a link target in a preview."""
    return url.lower().startswith(SAFE_PROTOCOLS) or not _SCHEME_LIKE.match(url)


def _safe_links(html: str) -> str:
    """Drop each link target, or picture source, that is not a safe URL."""

    def keep(m: re.Match[str]) -> str:
        url = html_lib.unescape(m[2])
        ok = safe_url(url) or (m[1] == "src" and url.lower().startswith("data:image/"))
        return m[0] if ok else ""

    return _URL_ATTR.sub(keep, html)


def valid_text(data: bytes, reject_wide: bool = True) -> str | None:
    """Decode bounded UTF-8 text, rejecting binary and wide lines."""
    try:
        if len(data) > SYNTAX_SIZE_LIMIT:
            return None
        text = data.decode("utf-8")
        if "\x00" in text:
            return None
        if (
            reject_wide
            and max((len(line) for line in text.splitlines()), default=0)
            > MAX_LINE_LENGTH
        ):
            return None
        return text
    except UnicodeDecodeError:
        return None


def read_text(path: Path, reject_wide: bool = True) -> str | None:
    """Read a bounded UTF-8 text file, rejecting binary and wide lines."""
    try:
        return valid_text(path.read_bytes(), reject_wide)
    except OSError:
        return None


def render_preview(
    path: Path,
    state=None,
    preview_url: str | None = None,
    lines: tuple[int, int] | None = None,
) -> str:
    """Return an HTML string (inner body fragment) for the given file path.

    This is the *rendered* representation: it dispatches on suffix, so
    reStructuredText arrives as HTML and a PDF as its viewer. ``render_source``
    below is the source side, but no route calls it: ``?filemill=highlight``
    serves the shell, and the browser shows the source. Markdown and .docx are
    not dispatched here: the browser renders them from the modules in
    ui/vendor/, so they fall through to coloured or raw source like any other
    text.

    *state* is accepted for callers that have a request's ``ViewState``; no
    renderer reads it since the Markdown renderer moved to the browser.
    *lines* is a 0-based, end-exclusive line span: a section of the file, as
    the browser's heading outline names one. Only reStructuredText honours it.
    """
    ext = _syntax_extension(path)
    preview = classify_path(path).preview

    if preview == "rst":
        return _preview_rst(path, lines)
    elif preview == "desktop":
        return _preview_desktop(path)
    elif preview == "pdf":
        return _preview_pdf(path, preview_url)
    elif preview == "html":
        return _preview_html(path, preview_url)
    elif preview == "image":
        return _preview_image(path, preview_url)
    else:
        # Try Pygments syntax highlighting (before raw text fallback)
        highlighted = _highlight_source(path, ext)
        if highlighted is not None:
            return highlighted
        # UTF-8 fallback: show any small-enough text file as raw <pre>
        raw = _raw_text(path)
        if raw is not None:
            return raw
        safe_ext = html_lib.escape(ext or "(no extension)")
        return f'<div class="preview-unsupported"><em>No preview available for {safe_ext} files.</em></div>'


def render_source(path: Path) -> str:
    """Return the file's own text, syntax-highlighted and never interpreted.

    ``render_preview`` dispatches on suffix, so a .html file becomes a page
    there. This returns the characters the author typed instead, coloured but
    not obeyed. Only tests call it: ``?filemill=highlight`` serves the shell,
    and the browser shows the source. Escaping happens in both branches below,
    so a file that contains markup shows that markup rather than running it.

    Falls through the same two steps as ``render_preview``: Pygments first, then
    a plain ``<pre>``, then an explicit "no source view" note for bytes that are
    not UTF-8 text.
    """
    ext = _syntax_extension(path)
    highlighted = _highlight_source(path, ext)
    if highlighted is not None:
        return highlighted
    raw = _raw_text(path)
    if raw is not None:
        return raw
    safe_ext = html_lib.escape(ext or "(no extension)")
    return (
        f'<div class="preview-unsupported">'
        f"<em>No source view available for {safe_ext} files.</em></div>"
    )


def _highlight_source(path: Path, ext: str) -> str | None:
    """Return Pygments-highlighted HTML, or None when it does not apply.

    None means one of: the file is over ``SYNTAX_SIZE_LIMIT``, it is not UTF-8,
    or no lexer other than ``TextLexer`` matched. Unrecognised plain text falls
    through to ``_raw_text`` rather than being wrapped in a pointless colour div.
    """
    try:
        if path.stat().st_size <= SYNTAX_SIZE_LIMIT:
            content = read_text(path, reject_wide=False)
            if content is not None:
                lexer = None
                try:
                    lexer = get_lexer_by_name(ext.lstrip("."))
                except ClassNotFound:
                    # No guess means no colour; retain the plain-text fallback.
                    with suppress(Exception):
                        lexer = guess_lexer(content)
                # Skip TextLexer – unrecognised plain text falls through to <pre>
                if lexer is not None and not isinstance(lexer, TextLexer):
                    formatter = PygHtmlFormatter(style="friendly", nowrap=False)
                    highlighted = pyg_highlight(content, lexer, formatter)
                    return f'<div class="preview-code">{highlighted}</div>'
    except Exception:
        # Colour is optional; the caller's plain-text fallback is not.
        return None
    return None


def _syntax_extension(path: Path) -> str:
    return ".py" if path.name.lower().endswith(".py.j2") else path.suffix.lower()


def _raw_text(path: Path) -> str | None:
    """Return a small-enough UTF-8 file as an escaped ``<pre>``, else None."""
    try:
        if path.stat().st_size <= RAW_SIZE_LIMIT:
            content = read_text(path, reject_wide=False)
            if content is not None:
                return f'<pre class="preview-raw">{html_lib.escape(content)}</pre>'
    except OSError:
        pass
    return None


def _preview_rst(path: Path, lines: tuple[int, int] | None = None) -> str:
    try:
        source = path.read_text(encoding="utf-8")
        if lines is not None:
            source = "\n".join(source.split("\n")[lines[0] : lines[1]])
        parts = publish_parts(
            source,
            writer_name="html5",
            settings_overrides={
                "raw_enabled": False,
                "file_insertion_enabled": False,
                "report_level": 5,
                "embed_stylesheet": False,
            },
        )
        title = (
            f"<h1>{html_lib.escape(parts['title'])}</h1>" if parts.get("title") else ""
        )
        body = title + _safe_links(parts["body"])
        return f'<div class="preview-rst">{body}</div>'
    except Exception as e:
        return (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )


def _preview_pdf(path: Path, preview_url: str | None = None) -> str:
    try:
        src = preview_url or f"/api/raw?p={urlquote(path.name)}"
        return f'<div class="preview-pdf"><iframe src="{src}"></iframe></div>'
    except Exception as e:  # pragma: no cover
        return (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )


def _preview_html(path: Path, preview_url: str | None = None) -> str:
    src = preview_url or f"/api/raw?p={urlquote(path.name)}"
    return f'<div class="preview-html"><iframe src="{src}"></iframe></div>'


def _preview_image(path: Path, preview_url: str | None = None) -> str:
    """The same ``pv-img`` the browser draws for an image on disk, so the
    shared stylesheet scales a member image to the pane the same way."""
    try:
        src = preview_url or f"/api/raw?p={urlquote(path.name)}"
        safe_name = html_lib.escape(path.name)
        return (
            '<div class="preview-image">'
            f'<img class="pv-img" src="{src}" alt="{safe_name}"></div>'
        )
    except Exception as e:  # pragma: no cover
        return (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )


def _preview_desktop(path: Path) -> str:
    """Preview a .desktop link file — show name, icon, and a clickable URL."""
    try:
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(str(path), encoding="utf-8")
        if "Desktop Entry" not in cp:
            return '<div class="preview-unsupported"><em>Not a valid .desktop file.</em></div>'
        entry = cp["Desktop Entry"]
        entry_type = entry.get("Type", "").strip()
        name = html_lib.escape(entry.get("Name", path.stem).strip())
        url = entry.get("URL", "").strip()
        icon = entry.get("Icon", "").strip()
        comment = html_lib.escape(entry.get("Comment", "").strip())

        if entry_type != "Link" or not url:
            return f'<div class="preview-unsupported"><em>Desktop entry type: {html_lib.escape(entry_type or "unknown")} — no URL to open.</em></div>'

        # Any other protocol is shown, not followed: a javascript: URL would run
        # as the page (A2).
        shown = html_lib.escape(url)
        link = (
            f'<a href="{shown}" target="_blank" rel="noopener noreferrer"'
            f' style="color:#4a9eff;">{shown}</a>'
            if safe_url(url)
            else shown
        )

        icon_html = ""
        if icon.startswith(("http://", "https://")):
            safe_icon = html_lib.escape(icon)
            icon_html = f'<img src="{safe_icon}" alt="" style="width:48px;height:48px;object-fit:contain;flex-shrink:0;">'

        comment_html = (
            f'<p style="margin:0;color:#aaa;font-size:0.9rem;">{comment}</p>'
            if comment
            else ""
        )

        return f"""<div class="preview-desktop-link" style="padding:2rem;display:flex;flex-direction:column;gap:1.2rem;">
  <div style="display:flex;align-items:center;gap:0.8rem;">
    {icon_html}<h2 style="margin:0;font-size:1.4rem;">{name}</h2>
  </div>
  {comment_html}
  <div style="word-break:break-all;">
    🔗 {link}
  </div>
</div>"""
    except Exception as e:
        return (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )
