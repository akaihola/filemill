# Milestone 05 – File previews and Markdown rendering

Clicking a file in a column should show a rich inline preview to the right.
This milestone builds two modules: `rendering.py` – a fully-configured
Markdown rendering pipeline with syntax highlighting, wikilinks, Mermaid
diagrams, and link normalisation – and `preview.py` – a dispatcher that
routes each file extension to the appropriate preview strategy.

## Markdown pipeline

We build a `MarkdownIt` instance with CommonMark defaults plus tables,
strikethrough, and plain-URL linkification. On top of that we layer
optional community plugins: front-matter stripping, footnotes, task
lists, heading anchors, definition lists, dollar-math, and admonitions.

### Core setup and syntax highlighting

The `highlight` callback receives fenced-code content and a language tag
from markdown-it-py and returns Pygments-highlighted HTML.

```python src/pykofinder/rendering.py
"""Markdown rendering, syntax highlighting, and link/wikilink resolution."""

import html as html_lib
from pathlib import Path
from urllib.parse import quote as urlquote

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.lexers.special import TextLexer

from pykofinder.styles import PYGMENTS_FORMATTER


def highlighter(code: str, lang: str, _attrs: str) -> str:
    try:
        lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
    except Exception:
        lexer = TextLexer()
    return highlight(code, lexer, PYGMENTS_FORMATTER)
```

### Git-root and file-resolution helpers

When a Markdown file references another file via a relative link or a
wikilink, we need to resolve that reference to an absolute path so we
can rewrite it as a pykofinder URL. The search strategy is:

1. Relative to the source file's parent directory.
2. Each ancestor up to the nearest `.git`-rooted ancestor.
3. Recursive `rglob` by basename inside the git root.

```python src/pykofinder/rendering.py +=


# ── Git-root and file-resolution helpers ──────────────────────────────────────


def _find_git_root(start: Path) -> Path | None:
    """Return the nearest ancestor of *start* (inclusive) containing a ``.git/`` dir."""
    for p in [start, *start.parents]:
        if (p / ".git").is_dir():
            return p
    return None


def _find_file_for_href(href: str, source_path: Path) -> Path | None:
    """Resolve a relative *href* to an absolute file path.

    Search order:

    1. Relative to *source_path*'s parent directory.
    2. Each ancestor directory up to and including the nearest ``.git``-rooted ancestor.
    3. Recursive ``rglob`` by basename inside that git-root directory.

    Returns ``None`` if the href is not relative or no matching file is found.
    """
    if not href:
        return None
    # Skip non-relative hrefs (absolute URLs, anchors, root-relative paths)
    if href.startswith(("http://", "https://", "#", "/", "mailto:", "ftp://")):
        return None

    # Strip URL fragment and query string
    clean = href.split("#")[0].split("?")[0]
    if not clean:
        return None

    # 1. Relative to source file's parent directory
    candidate = (source_path.parent / clean).resolve()
    if candidate.is_file():
        return candidate

    # Find git root – needed for steps 2 & 3
    git_root = _find_git_root(source_path.parent)
    if git_root is None:
        return None

    # 2. Each ancestor directory above source_path.parent, up to and including git_root.
    # (source_path.parent was already tried in step 1.)
    if source_path.parent != git_root:
        p = source_path.parent
        while True:
            p = p.parent
            candidate = (p / clean).resolve()
            if candidate.is_file():
                return candidate
            if p == git_root:
                break

    # 3. Recursive search by basename inside git_root, skipping hidden dirs
    filename = Path(clean).name
    for match in git_root.rglob(filename):
        # Skip anything inside a hidden directory (e.g. .git itself)
        if any(part.startswith(".") for part in match.relative_to(git_root).parts[:-1]):
            continue
        if match.is_file():
            return match

    return None


def _href_for_file(abs_path: Path) -> str:
    """Return a public pykofinder URL for a resolved file path.

    Markdown documents open through the finder UI (`/f/<mount>/<relative>`), while
    static assets use the raw named-mount path (`/w/<mount>/<relative>`) when the
    file is reachable from a known mount.
    """
    import pykofinder.app as app_module

    if abs_path.suffix.lower() == ".md":
        finder_url = app_module._finder_url(abs_path)
        if finder_url is not None:
            return finder_url
    web_url = app_module._web_url(abs_path)
    if web_url is not None:
        return web_url
    return f"/raw?path={urlquote(str(abs_path))}"
```

### MarkdownIt instance and plugins

Each plugin import is wrapped in a try/except so the renderer degrades
gracefully if any plugin is unavailable.

```python src/pykofinder/rendering.py +=


# ── MarkdownIt instance ────────────────────────────────────────────────────────

md = MarkdownIt("commonmark", {"highlight": highlighter, "linkify": True}).enable(
    ["table", "strikethrough", "linkify"]
)

# Optional plugins – graceful degradation if mdit_py_plugins is missing
try:
    from mdit_py_plugins.front_matter import front_matter_plugin

    front_matter_plugin(md)
except ImportError:  # pragma: no cover
    pass

try:
    from mdit_py_plugins.footnote import footnote_plugin

    footnote_plugin(md)
except ImportError:  # pragma: no cover
    pass

try:
    from mdit_py_plugins.tasklists import tasklists_plugin

    tasklists_plugin(md)
except ImportError:  # pragma: no cover
    pass

try:
    from mdit_py_plugins.anchors import anchors_plugin

    anchors_plugin(md)
except ImportError:  # pragma: no cover
    pass

try:
    from mdit_py_plugins.deflist import deflist_plugin

    deflist_plugin(md)
except ImportError:  # pragma: no cover
    pass

try:
    from mdit_py_plugins.dollarmath import dollarmath_plugin

    dollarmath_plugin(md)
except ImportError:  # pragma: no cover
    pass

try:
    from mdit_py_plugins.admon import admon_plugin

    admon_plugin(md)
except ImportError:  # pragma: no cover
    pass
```

### Mermaid fence renderer

Fenced code blocks tagged `mermaid` are rendered as `<div class="mermaid">`
instead of `<pre><code>`. The mermaid.js library (loaded from CDN in the
app shell) picks these up and renders them as SVG diagrams.

```python src/pykofinder/rendering.py +=


# ── Mermaid fence renderer ────────────────────────────────────────────────────


def _fence_rule(renderer, tokens, idx, options, env):
    """Mermaid fences produce ``<div class="mermaid">``.  All other fences unchanged."""
    token = tokens[idx]
    lang = token.info.strip().split()[0] if token.info.strip() else ""
    if lang == "mermaid":
        return f'<div class="mermaid">{html_lib.escape(token.content)}</div>\n'
    return renderer.__class__.fence(renderer, tokens, idx, options, env)


md.add_render_rule("fence", _fence_rule)
```

### Link normalisation

Relative links in Markdown files (like `./CONTRIBUTING.md`) are rewritten
to pykofinder URLs so clicking them navigates within the app instead of
hitting a 404.

```python src/pykofinder/rendering.py +=


# ── Link-normalization render rule ────────────────────────────────────────────


def _link_open_rule(renderer, tokens, idx, options, env):
    """Rewrite relative hrefs to pykofinder URLs when ``source_path`` is in *env*."""
    token = tokens[idx]
    source_path = env.get("source_path")
    if source_path is not None and token.attrs and "href" in token.attrs:
        found = _find_file_for_href(token.attrs["href"], source_path)
        if found is not None:
            token.attrs["href"] = _href_for_file(found)
    return renderer.renderToken(tokens, idx, options, env)


md.add_render_rule("link_open", _link_open_rule)
```

### Wikilinks

`[[Target]]` and `[[Target|Display]]` wikilinks are parsed by a custom
inline rule and rendered as `<a class="wikilink">` links. Resolution
tries the target as-is, then with `.md` appended.

```python src/pykofinder/rendering.py +=


# ── Wikilink inline plugin ────────────────────────────────────────────────────


def _wikilink_rule(state: StateInline, silent: bool) -> bool:
    """Parse ``[[Target]]`` and ``[[Target|Display]]`` wikilinks."""
    pos = state.pos
    src = state.src
    if src[pos : pos + 2] != "[[":
        return False
    end = src.find("]]", pos + 2)
    if end == -1:
        return False
    content = src[pos + 2 : end]
    if not content.strip():
        return False
    if "|" in content:
        target, display = content.split("|", 1)
    else:
        target = display = content
    if not silent:
        token = state.push("wikilink", "", 0)
        token.content = content
        token.meta = {"target": target.strip(), "display": display.strip()}
    state.pos = end + 2
    return True


def _wikilink_render(renderer, tokens, idx, options, env):
    """Render a wikilink token as ``<a class="wikilink" href="…">``."""
    token = tokens[idx]
    meta = token.meta
    target: str = meta["target"]
    display: str = meta["display"]

    source_path = env.get("source_path")
    href = None
    if source_path is not None:
        # Try the target as-is, then appended with .md
        for candidate in (target, target + ".md"):
            found = _find_file_for_href(candidate, source_path)
            if found is not None:
                href = _href_for_file(found)
                break

    if href is None:
        href = f"#wikilink-{urlquote(target)}"

    return (
        f'<a href="{html_lib.escape(href)}" class="wikilink">'
        f"{html_lib.escape(display)}</a>"
    )


md.add_render_rule("wikilink", _wikilink_render)
# Insert before the 'link' rule so [[…]] is consumed before normal link tokenization
md.inline.ruler.before("link", "wikilink", _wikilink_rule)
```

## Preview dispatcher

The preview module examines a file's extension and delegates to the
appropriate rendering strategy. Unrecognised extensions fall through to
Pygments syntax highlighting (if a lexer can be guessed), then to a raw
`<pre>` block, and finally to an "unsupported" placeholder.

```python src/pykofinder/preview.py
import configparser
import html as html_lib
from pathlib import Path
from urllib.parse import quote as urlquote


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def render_preview(path: Path) -> str:
    """Return an HTML string (inner body fragment) for the given file path."""
    ext = path.suffix.lower()

    if ext == ".desktop":
        return _preview_desktop(path)
    elif ext == ".md":
        return _preview_md(path)
    elif ext == ".docx":
        return _preview_docx(path)
    elif ext == ".pptx":
        return _preview_pptx(path)
    elif ext == ".pdf":
        return _preview_pdf(path)
    elif ext in IMAGE_EXTS:
        return _preview_image(path)
    else:
        # Try Pygments syntax highlighting (before raw text fallback)
        SYNTAX_SIZE_LIMIT = 512 * 1024  # 512 KB
        try:
            from pygments import highlight as pyg_highlight
            from pygments.formatters import HtmlFormatter as PygHtmlFormatter
            from pygments.lexers import (
                ClassNotFound,
                TextLexer,
                get_lexer_by_name,
                guess_lexer,
            )

            if path.stat().st_size <= SYNTAX_SIZE_LIMIT:
                try:
                    content = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    content = None
                if content is not None:
                    lexer = None
                    try:
                        lexer = get_lexer_by_name(ext.lstrip("."))
                    except ClassNotFound:
                        try:
                            lexer = guess_lexer(content)
                        except Exception:
                            pass
                    # Skip TextLexer – unrecognised plain text falls through to <pre>
                    if lexer is not None and not isinstance(lexer, TextLexer):
                        formatter = PygHtmlFormatter(style="friendly", nowrap=False)
                        highlighted = pyg_highlight(content, lexer, formatter)
                        return f'<div class="preview-code">{highlighted}</div>'
        except Exception:
            pass
        # UTF-8 fallback: show any small-enough text file as raw <pre>
        if path.stat().st_size <= 256 * 1024:
            try:
                content = path.read_text(encoding="utf-8")
                return f'<pre class="preview-raw">{html_lib.escape(content)}</pre>'
            except UnicodeDecodeError:
                pass
        safe_ext = html_lib.escape(ext or "(no extension)")
        return f'<div class="preview-unsupported"><em>No preview available for {safe_ext} files.</em></div>'
```

### Markdown preview

Delegates to the `md` renderer from `rendering.py`, passing the file's
path through the `env` dict so that link normalisation and wikilink
resolution know where to search for relative targets.

```python src/pykofinder/preview.py +=


def _preview_md(path: Path) -> str:
    try:
        from pykofinder.rendering import md as md_renderer

        html_body = md_renderer.render(
            path.read_text(encoding="utf-8"), {"source_path": path}
        )
        return f'<div class="preview-md">{html_body}</div>'
    except Exception as e:
        return (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )
```

### DOCX and PPTX previews

DOCX files are converted to HTML by **mammoth**. PPTX files are walked
slide-by-slide using **python-pptx**, extracting text from every shape's
text frame.

```python src/pykofinder/preview.py +=


def _preview_docx(path: Path) -> str:
    try:
        import mammoth

        with open(path, "rb") as f:
            result = mammoth.convert_to_html(f)
        return f'<div class="preview-docx">{result.value}</div>'
    except Exception as e:
        return (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )


def _preview_pptx(path: Path) -> str:
    try:
        from pptx import Presentation

        prs = Presentation(str(path))
        slides_html = []
        for i, slide in enumerate(prs.slides, 1):
            parts = [f'<div class="slide"><h3>Slide {i}</h3>']
            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                for para in shape.text_frame.paragraphs:
                    line_parts = []
                    for run in para.runs:
                        text = html_lib.escape(run.text)
                        if run.font.bold:
                            text = f"<strong>{text}</strong>"
                        if run.font.italic:
                            text = f"<em>{text}</em>"
                        line_parts.append(text)
                    if line_parts:
                        parts.append(f"<p>{''.join(line_parts)}</p>")
            parts.append("</div>")
            slides_html.append("".join(parts))
        return f'<div class="preview-pptx">{"".join(slides_html)}</div>'
    except Exception as e:
        return (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )
```

### PDF and image previews

PDFs are shown in an `<iframe>` pointing at the `/raw` endpoint. Images
use the same endpoint as an `<img>` source, displayed on a checkerboard
background (styled in Milestone 2) so transparency is visible.

```python src/pykofinder/preview.py +=


def _preview_pdf(path: Path) -> str:
    try:
        src = f"/raw?path={urlquote(str(path))}"
        return f'<div class="preview-pdf"><iframe src="{src}"></iframe></div>'
    except Exception as e:  # pragma: no cover
        return (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )


def _preview_image(path: Path) -> str:
    try:
        src = f"/raw?path={urlquote(str(path))}"
        safe_name = html_lib.escape(path.name)
        return f'<div class="preview-image"><img src="{src}" alt="{safe_name}"></div>'
    except Exception as e:  # pragma: no cover
        return (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )
```

### Desktop file preview

`.desktop` link files (FreeDesktop standard) contain a URL, name, icon,
and comment. We parse them with `configparser` and render a card with
the link information and an "Open →" button.

```python src/pykofinder/preview.py +=


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

        safe_url = html_lib.escape(url)
        open_href = f"/open-link?path={urlquote(str(path))}"

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
    🔗 <a href="{safe_url}" target="_blank" rel="noopener noreferrer"
          style="color:#4a9eff;">{safe_url}</a>
  </div>
  <div>
    <a href="{open_href}" target="_blank" rel="noopener noreferrer"
       style="display:inline-block;padding:0.5rem 1.2rem;background:#4a9eff;color:#fff;border-radius:4px;text-decoration:none;font-weight:600;">
      Open →
    </a>
  </div>
</div>"""
    except Exception as e:
        return (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )
```

## Verification

```bash
rm -rf _tangle_out && mkdir _tangle_out && cd _tangle_out
lmt ../01-*.md ../02-*.md ../03-*.md ../04-*.md ../05-*.md
uv sync
python -c "
from pykofinder.rendering import md
html = md.render('# Hello\n\nA [link](foo.md) and a \`\`\`python\nprint(1)\n\`\`\` block.')
print(html[:200])
"
```
