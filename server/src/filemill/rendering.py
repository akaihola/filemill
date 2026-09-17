"""Markdown rendering and link/wikilink resolution.

Fenced code is emitted as ``<pre><code class="language-x">`` and coloured in the
browser by ``ui/core/syntax.js`` — one implementation for both builds.
"""

import html as html_lib
from pathlib import Path
from urllib.parse import quote as urlquote

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline

from filemill import urls

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
    clean = href.split("#")[0].split("?")[0]
    if clean.startswith("~/"):
        candidate = Path.home() / clean[2:]
        return candidate.resolve() if candidate.is_file() else None
    # Skip non-relative hrefs (absolute URLs, anchors, root-relative paths)
    if href.startswith(("http://", "https://", "#", "/", "mailto:", "ftp://")):
        return None

    # Strip URL fragment and query string
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


def _href_for_file(abs_path: Path, state=None) -> str:
    """Return a public filemill URL for a resolved file path.

    The URL is the file's path relative to the configured root. A Markdown
    document adds ``?filemill=render``, because a link from one document
    to another should land on the rendered document rather than download its
    source. Everything else uses the bare path, which serves the bytes — so an
    ``![image](photo.png)`` in Markdown resolves to ``/photo.png`` and renders.

    *state* is the request's ``ViewState`` when one is known. Its layout and
    dotfile choices ride along, so following a link inside an embedded
    ``layout=no-columns`` document does not dump the reader into the full finder.
    The state's ``vpath`` is deliberately not carried: it addresses a node inside
    the *source* document and means nothing in the target.

    Falls back to the named-mount ``/w/`` URL, then to ``/raw?path=``, for a file
    with no root-relative address at all — a standalone bookmark mount target
    reached from outside the visible tree.
    """
    import filemill.app as app_module

    rel = app_module._rel_url_path(abs_path)
    if rel is not None:
        layout = None
        if state is not None:
            layout = state.layout if state.layout != urls.DEFAULT_LAYOUT else None
        view = urls.VIEW_RENDER if abs_path.suffix.lower() == ".md" else None
        return urls.build_url(rel, view=view, layout=layout)

    web_url = app_module._web_url(abs_path)
    if web_url is not None:
        return web_url
    return f"/raw?path={urlquote(str(abs_path))}"


# ── MarkdownIt instance ────────────────────────────────────────────────────────

md = MarkdownIt("commonmark", {"linkify": True}).enable(
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
    """Rewrite relative hrefs to filemill URLs when ``source_path`` is in *env*."""
    token = tokens[idx]
    source_path = env.get("source_path")
    if source_path is not None and token.attrs and "href" in token.attrs:
        found = _find_file_for_href(token.attrs["href"], source_path)
        if found is not None:
            token.attrs["href"] = _href_for_file(found, env.get("view_state"))
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
                href = _href_for_file(found, env.get("view_state"))
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
