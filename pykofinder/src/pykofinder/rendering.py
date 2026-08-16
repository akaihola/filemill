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


# ── #21 Mermaid fence renderer ────────────────────────────────────────────────


def _fence_rule(renderer, tokens, idx, options, env):
    """Mermaid fences produce ``<div class="mermaid">``.  All other fences unchanged."""
    token = tokens[idx]
    lang = token.info.strip().split()[0] if token.info.strip() else ""
    if lang == "mermaid":
        return f'<div class="mermaid">{html_lib.escape(token.content)}</div>\n'
    return renderer.__class__.fence(renderer, tokens, idx, options, env)


md.add_render_rule("fence", _fence_rule)


# ── #19 Link-normalization render rule ────────────────────────────────────────


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


# ── #20 Wikilink inline plugin ────────────────────────────────────────────────


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
