import configparser
import html as html_lib
import json
import os
from pathlib import Path
from textwrap import dedent
from urllib.parse import quote as urlquote
from urllib.parse import unquote as urlunquote

from fasthtml.common import (
    Body,
    Div,
    Head,
    Html,
    Link,
    Meta,
    NotStr,
    Script,
    Style,
    Title,
    fast_app,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
)

from filemill import api, urls
from filemill.columns import (
    initial_columns,
    list_column,
    list_vfs_column,
    render_breadcrumb,
)
from filemill.env import env
from filemill.preview import render_preview, render_source
from filemill.styles import APP_CSS, COLUMN_JS, LIVE_RELOAD_JS
from filemill.vfs import REGISTRY

# CDN URL for mermaid.js (UMD build – sets window.mermaid on load)
_MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"

# Static files bundled with the package (PWA manifest, service worker, icons)
_STATIC_DIR: Path = Path(__file__).parent / "static"

# Inline JS injected into every page to register the service worker
_SW_REGISTER_JS: str = dedent("""\
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js', {scope: '/'});
    }
""")

# HTML file extensions that get a "View as web page" button in the preview
_HTML_EXTS = {".html", ".htm"}

# Overridden by cli.py before serve() is called; also supports env var for reload mode
ROOT: Path = Path(env("ROOT", str(Path.home())))

LIVE_MODE: bool = env("LIVE").lower() in ("1", "true", "yes")

app, rt = fast_app(
    hdrs=(
        Style(APP_CSS),
        Script(COLUMN_JS),
    ),
    pico=False,
    live=False,
)


def _resolve_safe(path_str: str, root: Path | None = None) -> Path | None:
    """Resolve a user-supplied path and verify it falls within an allowed zone.

    Allowed zones
    -------------
    1. ROOT itself – any real file or directory that lives under ROOT.
    2. The resolved target of any *direct* symlink child of ROOT – lets
       directory symlinks placed in ROOT act as bookmarks whose subtrees are
       fully browsable.

    Symlinks *within* a bookmark subtree are only allowed when their resolved
    target falls inside zone 1 or the same zone-2 directory (or another
    bookmark target).  Symlinks that escape all allowed zones are denied.

    Path-traversal via ``..`` is defeated because the containment check
    operates on the fully-resolved path, not the raw string.
    """
    effective_root = root if root is not None else ROOT
    try:
        resolved_root = effective_root.resolve()
        resolved = Path(os.path.normpath(urlunquote(path_str))).resolve()

        # Zone 1: within ROOT
        try:
            resolved.relative_to(resolved_root)
            return resolved
        except ValueError:
            pass

        # Zone 2: within the resolved target of a direct symlink child of ROOT
        for child in effective_root.iterdir():
            if child.is_symlink():
                target = child.resolve()
                try:
                    resolved.relative_to(target)
                    return resolved
                except ValueError:
                    continue

        return None
    except Exception:
        return None


def _head_tags(*extra_head_scripts):
    """Return the ``<head>`` every Filemill page shares."""
    extra_scripts = [Script(LIVE_RELOAD_JS)] if LIVE_MODE else []
    return Head(
        Title("Filemill"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="theme-color", content="#0770C9"),
        Meta(name="mobile-web-app-capable", content="yes"),
        Meta(name="apple-mobile-web-app-capable", content="yes"),
        Meta(
            name="apple-mobile-web-app-status-bar-style",
            content="black-translucent",
        ),
        Meta(name="apple-mobile-web-app-title", content="filemill"),
        Link(rel="manifest", href="/manifest.json"),
        Link(rel="apple-touch-icon", href="/icons/icon-192.png"),
        Style(APP_CSS),
        Script(src="https://unpkg.com/htmx.org@1.9.12"),
        Script(src=_MERMAID_CDN),
        Script(COLUMN_JS),
        Script(_SW_REGISTER_JS),
        *extra_scripts,
        *extra_head_scripts,
    )


def _shell_html(*extra_head_scripts):
    """Return the full app-shell HTML page."""
    return Html(_head_tags(*extra_head_scripts), Body(initial_columns(ROOT)))


def _page_html(body_children, state, *extra_head_scripts):
    """Wrap body content in a full page whose ``<body>`` carries the layout.

    The layout is an attribute, not a second template. ``compressed-columns``
    reuses the ``zoomed`` presentation the ⛶ button already toggles, and
    The .* button and localStorage preference control dotfile visibility in the
    browser; it is not part of the resource URL contract.

    ``data-layout`` is set so the client can read the requested state back.
    """
    classes = []
    if state.layout == urls.LAYOUT_COMPRESSED:
        classes.append("zoomed")
    attrs = {"cls": " ".join(classes)} if classes else {}
    return Html(
        _head_tags(*extra_head_scripts),
        Body(
            *body_children,
            data_layout=state.layout,
            **attrs,
        ),
    )


@rt("/")
def index():
    """Redirect root to the finder namespace."""
    return RedirectResponse("/f/", status_code=302)


@rt("/sse/reload")
async def sse_reload():
    """Server-Sent Events stream; emits a reload event when files under ROOT change."""
    if not LIVE_MODE:
        from starlette.responses import Response

        return Response(status_code=404)

    import asyncio

    from starlette.responses import StreamingResponse

    async def event_generator():
        try:
            from watchfiles import awatch

            async for _changes in awatch(str(ROOT)):
                yield "data: reload\n\n"
        except Exception:
            # If watchfiles not available or error, just keep stream open
            while True:
                await asyncio.sleep(30)
                yield ": keepalive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _make_bc_oob(path: Path, vpath: str = "") -> str:
    """Return breadcrumb HTML string with hx-swap-oob="true" set."""
    return render_breadcrumb(path, ROOT, vpath).replace(
        '<nav id="breadcrumb">', '<nav id="breadcrumb" hx-swap-oob="true">'
    )


def _build_prune_js(col: int) -> str:
    """Return a <script> that prunes sibling columns ≥ col and restores sentinel."""
    return dedent(f"""\
        <script>
        (function(){{
            var el = document.getElementById('col-{col}');
            while (el && el.id !== 'preview') {{
                var next = el.nextElementSibling;
                el.remove();
                el = next;
            }}
            var sentinel = document.createElement('div');
            sentinel.id = 'col-{col}';
            var preview = document.getElementById('preview');
            if (preview) preview.parentNode.insertBefore(sentinel, preview);
        }})();
        </script>""")


@rt("/click")
def click(path: str, col: int, vpath: str = "", fmt: str = "", leaf: bool = False):
    """Handle click on a directory, file, or VFS entry."""
    p = _resolve_safe(path)
    if p is None:
        return Div(
            "Access denied.",
            id=f"col-{col}",
            cls="column",
            style="color:#c00; padding:1rem;",
        )

    # ── VFS dispatch ──────────────────────────────────────────────────────────
    provider = REGISTRY.get(p)
    if provider is not None:
        resolved_fmt = fmt or provider.default_fmt(vpath)
        entries = provider.list_entries(p, vpath)

        if resolved_fmt == "spreadsheet":
            # Spreadsheet mode: collapse column to sentinel, OOB-update preview
            try:
                preview_html = provider.render_preview(
                    p, vpath, "spreadsheet", page=1, limit=1000, col=col
                )
            except Exception as exc:
                preview_html = (
                    f'<div class="preview-error">'
                    f"Preview error: {html_lib.escape(str(exc))}</div>"
                )
            sentinel = Div(id=f"col-{col}")
            preview_oob = NotStr(
                f'<div id="preview" hx-swap-oob="true">{preview_html}</div>'
            )
            bc_oob = NotStr(_make_bc_oob(p, vpath))
            return sentinel, preview_oob, bc_oob

        elif not entries:
            # No children at this vpath – either a true leaf (row detail) or an empty
            # folder (e.g. an empty table).  The two cases differ in the HTMX target:
            #   leaf=True  → request targets #preview with innerHTML
            #   leaf=False → request targets #col-{col} with outerHTML
            # leaf=1 is added to the hx-get URL of non-folder VFS entries in
            # list_vfs_column so the server can tell them apart.
            try:
                preview_html = provider.render_preview(
                    p, vpath, resolved_fmt, page=1, limit=1000, col=col
                )
            except Exception as exc:
                preview_html = (
                    f'<div class="preview-error">'
                    f"Preview error: {html_lib.escape(str(exc))}</div>"
                )
            bc_oob = NotStr(_make_bc_oob(p, vpath))
            if leaf:
                # True leaf: the response goes directly into #preview via innerHTML.
                # Include prune_js to clean up any stale right-hand columns.
                prune_js = _build_prune_js(col)
                return NotStr(preview_html + prune_js + _make_bc_oob(p, vpath))
            else:
                # Empty folder (e.g. empty table): request targeted #col-{col} via
                # outerHTML.  Return a sentinel for that slot and push the preview
                # content out-of-band into #preview.
                sentinel = NotStr(
                    f'<div id="col-{col}"></div>' + _build_prune_js(col + 1)
                )
                preview_oob = NotStr(
                    f'<div id="preview" hx-swap-oob="true">{preview_html}</div>'
                )
                return sentinel, preview_oob, bc_oob

        else:
            # Column mode: show entries as a column (tables or row listing)
            show_fmt_bar = any(e.icon == "📋" for e in entries)
            encoded_path = urlquote(str(p))
            new_col = list_vfs_column(
                entries=entries,
                fs_path_encoded=encoded_path,
                fs_path_raw=str(p),
                vpath=vpath,
                col_index=col,
                show_fmt_bar=show_fmt_bar,
                active_fmt=resolved_fmt,
                ext=p.suffix.lower(),
            )
            preview_clear = Div(id="preview", hx_swap_oob="true")
            bc_oob = NotStr(_make_bc_oob(p, vpath))
            return new_col, preview_clear, bc_oob

    # ── Real directory ────────────────────────────────────────────────────────
    if p.is_dir():
        # Return new column as main swap target; preview and breadcrumb cleared via OOB
        bc_oob = render_breadcrumb(p, ROOT).replace(
            '<nav id="breadcrumb">', '<nav id="breadcrumb" hx-swap-oob="true">'
        )
        new_col = list_column(p, ROOT, col_index=col)
        preview_clear = Div(id="preview", hx_swap_oob="true")
        return new_col, preview_clear, NotStr(bc_oob)

    # ── Regular file preview ──────────────────────────────────────────────────
    try:
        preview_html = render_preview(p)
    except Exception as e:
        preview_html = (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )
    # For HTML files prepend a "View as web page" button
    if p.suffix.lower() in _HTML_EXTS:
        web_url = _web_url(p)
        if web_url:
            preview_html = (
                f'<div class="preview-webmode-bar">'
                f'<a href="{html_lib.escape(web_url)}" target="_blank"'
                f' rel="noopener noreferrer">🌐 View as web page</a></div>'
            ) + preview_html
    # Prune columns col-{col} and beyond (left over from prior directory navigation),
    # then recreate the col-{col} sentinel.
    prune_js = _build_prune_js(col)
    bc_oob = render_breadcrumb(p, ROOT).replace(
        '<nav id="breadcrumb">', '<nav id="breadcrumb" hx-swap-oob="true">'
    )
    return NotStr(preview_html + prune_js + bc_oob)


@rt("/vpage")
def vpage(path: str, vpath: str, page: int = 1, limit: int = 1000):
    """Return a paginated spreadsheet fragment for the given VFS table (target: #preview)."""
    p = _resolve_safe(path)
    if p is None or not p.is_file():
        return HTMLResponse("Not found", status_code=404)
    provider = REGISTRY.get(p)
    if provider is None:
        return HTMLResponse("Not found", status_code=404)
    try:
        html = provider.render_preview(
            p, vpath, fmt="spreadsheet", page=page, limit=limit, col=0
        )
    except Exception as exc:
        html = (
            f'<div class="preview-error">'
            f"Preview error: {html_lib.escape(str(exc))}</div>"
        )
    return NotStr(html)


@rt("/raw")
def raw(path: str):
    """Serve raw file bytes (used by PDF iframe)."""
    p = _resolve_safe(path)
    if p is None or not p.is_file():
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(str(p))


def _parse_desktop_url(path: Path) -> str | None:
    """Parse a .desktop file and return URL if Type=Link, else None."""
    try:
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(str(path), encoding="utf-8")
        if "Desktop Entry" in cp:
            entry = cp["Desktop Entry"]
            if entry.get("Type", "").strip() == "Link":
                url = entry.get("URL", "").strip()
                return url or None
    except Exception:  # noqa: S110 — a malformed .desktop file simply has no URL
        pass
    return None


@rt("/restore")
def restore(path: str, vpath: str = ""):
    """Return a full app-shell HTML for the given path (deep-link restoration)."""
    p = _resolve_safe(path)
    if p is None:
        # Fall back to root view
        shell = initial_columns(ROOT)
        return HTMLResponse(repr(shell))
    return HTMLResponse(_finder_fragment(p, vpath))


def _finder_fragment(
    p: Path, vpath: str = "", preview_override: str | None = None
) -> str:
    """Return the ``#app-shell`` fragment: columns down to *p*, plus its preview.

    Three callers share this one builder — the ``/restore`` deep link, the
    root-relative finder page, and the same page embedded in the dashboard — so a
    column that appears in one of them appears in all three. That is the whole
    reason it was lifted out of ``restore()``.

    *preview_override* replaces what fills the preview pane. It is how
    ``?filemill=`` picks a representation without a second shell template:
    the columns are the same, only the pane differs.
    """
    # Build ancestor chain: ROOT plus each directory step down to p
    try:
        rel = p.relative_to(ROOT)
        parts = list(rel.parts)
    except ValueError:
        # Zone-2 path: p lives inside the resolved target of a direct symlink
        # child of ROOT.  Build parts as [symlink_name, *sub_path_parts] so
        # that all intermediate columns (ROOT → bookmark → … → p) are rendered.
        parts = None
        for child in ROOT.iterdir():
            if child.is_symlink():
                target = child.resolve()
                try:
                    rel_in_target = p.relative_to(target)
                    parts = [child.name] + list(rel_in_target.parts)
                    break
                except ValueError:
                    continue
        if parts is None:
            parts = [p.name]  # fallback: p is exactly the symlink target

    dirs: list[Path] = []
    cur = ROOT
    for part in parts:
        dirs.append(cur)
        cur = cur / part
    if cur.is_dir():
        dirs.append(cur)

    cols_html = ""
    for i, d in enumerate(dirs):
        if d.is_dir():  # pragma: no branch – dirs only ever contains directories
            sel = parts[i] if i < len(parts) else None
            col_obj = list_column(d, ROOT, col_index=i, selected_name=sel)
            cols_html += repr(col_obj)

    sentinel_idx = len([d for d in dirs if d.is_dir()])
    sentinel_html = f'<div id="col-{sentinel_idx}"></div>'

    preview_html = ""
    if p.is_file():
        provider = REGISTRY.get(p)
        if provider is not None:
            # VFS-backed file (e.g. SQLite .db): walk vpath segments, rendering
            # one column per level, then show a preview at the leaf.
            encoded_path = urlquote(str(p))
            vpath_parts = [seg for seg in vpath.split("/") if seg]
            for i in range(len(vpath_parts) + 1):
                current_vpath = "/".join(vpath_parts[:i])
                selected_vpath = (
                    "/".join(vpath_parts[: i + 1]) if i < len(vpath_parts) else None
                )
                entries = provider.list_entries(p, current_vpath)
                if not entries:
                    # Leaf or empty node: render preview regardless of vpath depth
                    # (e.g. JSON files have no navigable children even at root vpath).
                    if preview_override is not None:
                        preview_html = preview_override
                        break
                    try:
                        preview_html = provider.render_preview(
                            p, current_vpath, "folders", 1, 1000, col=sentinel_idx
                        )
                    except Exception as exc:
                        preview_html = f'<div class="preview-error">{html_lib.escape(str(exc))}</div>'
                    break
                show_fmt_bar = any(e.icon == "📋" for e in entries)
                vfs_col = list_vfs_column(
                    entries=entries,
                    fs_path_encoded=encoded_path,
                    fs_path_raw=str(p),
                    vpath=current_vpath,
                    col_index=sentinel_idx,
                    show_fmt_bar=show_fmt_bar,
                    active_fmt=provider.default_fmt(current_vpath),
                    ext=p.suffix.lower(),
                    selected_vpath=selected_vpath,
                )
                cols_html += repr(vfs_col)
                sentinel_idx += 1
            sentinel_html = f'<div id="col-{sentinel_idx}"></div>'
        elif preview_override is not None:
            preview_html = preview_override
        else:
            try:
                preview_html = render_preview(p)
            except Exception as e:
                preview_html = (
                    f'<div class="preview-error">{html_lib.escape(str(e))}</div>'
                )
            # For HTML files prepend a "View as web page" button (mirrors /click)
            if p.suffix.lower() in _HTML_EXTS:
                web_url = _web_url(p)
                if web_url:
                    preview_html = (
                        f'<div class="preview-webmode-bar">'
                        f'<a href="{html_lib.escape(web_url)}" target="_blank"'
                        f' rel="noopener noreferrer">🌐 View as web page</a></div>'
                    ) + preview_html

    preview_cls = "" if preview_html else "preview-empty"
    preview_div = f'<div id="preview" class="{preview_cls}">{preview_html}</div>'
    bc_html = render_breadcrumb(p, ROOT)

    return (
        f'<div id="app-shell">{bc_html}'
        f'<div id="finder">{cols_html}{sentinel_html}{preview_div}</div></div>'
    )


@rt("/open-link")
def open_link(path: str):
    """Redirect the browser to the URL stored in a .desktop link file."""
    p = _resolve_safe(path)
    if p is None or not p.is_file():
        return HTMLResponse("Not found", status_code=404)
    url = _parse_desktop_url(p)
    if not url:
        return HTMLResponse("Not a .desktop link file", status_code=400)
    return RedirectResponse(url, status_code=302)


# ── #23 helpers + routes ──────────────────────────────────────────────────────


def _mount_targets() -> dict[str, Path]:
    """Return named mounts exposed under ``/w/<mount>/...``.

    The root directory itself is always mounted under ``ROOT.name``. Each direct
    symlink child of ``ROOT`` is also mounted under the symlink name.
    """
    mounts = {ROOT.name: ROOT.resolve()}
    for child in ROOT.iterdir():
        if child.is_symlink():
            mounts[child.name] = child.resolve()
    return mounts


def _resolve_web_mount(path: str) -> Path | None:
    """Resolve a ``/w/`` path using named mounts.

    The first path segment names either the root mount (``ROOT.name``) or one of
    ROOT's direct symlink children. The remainder is resolved relative to that
    mount target and still validated through ``_resolve_safe()``.
    """
    stripped = path.lstrip("/")
    if not stripped:
        return None

    mount_name, _, remainder = stripped.partition("/")
    target_root = _mount_targets().get(mount_name)
    if target_root is None:
        return None

    candidate = target_root / remainder if remainder else target_root
    return _resolve_safe(str(candidate))


def _mounted_path_parts(p: Path) -> tuple[str, Path] | None:
    """Return ``(mount_name, relative_path)`` for a resolved path, or ``None``.

    Canonical URL generation for both ``/w/`` and ``/f/`` shares the same named-mount
    mapping. Prefer the visible ROOT tree, including descendants reached through direct
    symlink children, then fall back to standalone bookmark mounts.
    """
    effective_root = ROOT
    mounts = _mount_targets()
    root_mount = ROOT.name
    resolved_root = mounts[root_mount]

    try:
        rel_from_root = p.relative_to(resolved_root)
        visible_candidate = effective_root / rel_from_root
        if (
            visible_candidate.exists()
            and (visible_candidate == p or visible_candidate.resolve() == p)
        ) or not rel_from_root.parts:
            return root_mount, rel_from_root
    except ValueError:
        pass

    for child in effective_root.iterdir():
        if not child.is_symlink():
            continue
        try:
            rel_from_child = p.relative_to(child.resolve())
        except ValueError:
            continue
        visible_rel = (
            Path(child.name) / rel_from_child
            if rel_from_child.parts
            else Path(child.name)
        )
        return root_mount, visible_rel

    for mount_name, target in mounts.items():
        if mount_name == root_mount:
            continue
        try:
            return mount_name, p.relative_to(target)
        except ValueError:
            continue
    return None


def _finder_url(p: Path, vpath: str = "") -> str | None:
    """Return a canonical ``/f/`` URL for *p*, optionally preserving *vpath*."""
    mounted = _mounted_path_parts(p)
    if mounted is None:
        return None
    mount_name, rel = mounted
    url = f"/f/{mount_name}/{rel}"
    if vpath:
        url += f"?vpath={urlquote(vpath)}"
    return url


def _web_url(p: Path) -> str | None:
    """Return a canonical ``/w/`` URL for *p*, or ``None`` if it is unreachable."""
    mounted = _mounted_path_parts(p)
    if mounted is None:
        return None
    mount_name, rel = mounted
    return f"/w/{mount_name}/{rel}"


@rt("/w/{path:path}")
def web_static(path: str):
    """Serve a named-mount ``/w/<mount>/...`` file with the correct Content-Type."""
    p = _resolve_web_mount(path)
    if p is None or not p.is_file():
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(str(p))


@rt("/f/")
def finder_root(path: str = "", vpath: str = ""):
    """Serve the finder root or redirect legacy ``/f/?path=...`` deep-links."""
    if path:
        p = _resolve_safe(path)
        if p is None or not p.exists():
            return HTMLResponse("Not found", status_code=404)
        canonical = _finder_url(p, vpath)
        if canonical is not None:
            return RedirectResponse(canonical, status_code=302)
        nav_js = (
            f"document.addEventListener('DOMContentLoaded',"
            f"function(){{_deepNavigate({json.dumps(str(p))}, {json.dumps(vpath or None)})}});"
        )
        return _shell_html(Script(nav_js))
    return _shell_html()


@rt("/f/{path:path}")
def finder_view(path: str = "", vpath: str = ""):
    """Serve the finder shell at an optional canonical mount-relative path.

    ``/f/`` renders the root view.
    ``/f/<mount>/<relative>`` renders the shell and deep-links to that file.
    """
    if not path:
        return _shell_html()

    mount_name, _, remainder = path.lstrip("/").partition("/")
    target_root = _mount_targets().get(mount_name)
    if target_root is None:
        return HTMLResponse("Not found", status_code=404)

    candidate = target_root / remainder if remainder else target_root
    p = _resolve_safe(str(candidate))
    if p is None or not p.exists():
        return HTMLResponse("Not found", status_code=404)

    nav_js = (
        f"document.addEventListener('DOMContentLoaded',"
        f"function(){{_deepNavigate({json.dumps(str(p))}, {json.dumps(vpath or None)})}});"
    )
    return _shell_html(Script(nav_js))


# ── The shared Miller-columns UI ─────────────────────────────────────────────
#
# ui/ is a copy of the repository's shared frontend at ../../../ui, made by
# tools/sync-ui.py so a wheel carries what it needs at runtime — see
# ui/adapters/README.md. filemill builds its single file from that same
# directory, which is what makes these the same app rather than two that
# resemble each other. Its core/ is source-agnostic; the adapters loaded below
# point it at this server. Nothing under ui/ is edited here, ever.
#
# Mounted under /n/ during the migration, so the HTMX UI at /f/ keeps working.
# Cutting over is changing UI_BASE to "/" and letting the catch-all serve the
# shell — at which point the URL path *is* the file path relative to ROOT, with
# no prefix at all.

UI_BASE = "/n/"
_UI_DIR: Path = Path(__file__).parent / "ui"

_UI_CORE = [
    "shell.js", "ports.js", "icons.js", "state.js", "sort.js", "render.js",
    "layout.js", "trail.js", "typeahead.js", "nav.js", "deeplink.js",
    "settings.js",
]

# Load order is dependency order. Both filesystem adapters are present because
# "Open local folder…" switches between them at runtime; app-http.js is what
# selects, so the order of the adapter files themselves does not matter.
_UI_ADAPTERS = [
    "http.js", "preview-http.js", "preview-local.js", "preview-upload.js",
    "router-path.js", "fsa.js", "storage.js", "app-http.js",
]


@rt("/ui/{path:path}")
def ui_asset(path: str):
    """Serve a vendored UI file."""
    parts = [p for p in path.split("/") if p not in ("", ".", "..")]
    target = _UI_DIR.joinpath(*parts)
    if len(parts) < 2 or not target.is_file():
        return HTMLResponse("Not found", status_code=404)
    media = {
        ".js": "application/javascript",
        ".css": "text/css",
        ".woff": "font/woff",
    }.get(target.suffix, "application/octet-stream")
    return FileResponse(str(target), media_type=media)


def _ui_shell(state, base: str):
    """The app shell for the shared UI. Deliberately almost empty.

    The chrome is built by ui/core/shell.js so that this page and filemill's
    index.html cannot drift apart — there is no markup here to keep in step.

    The view and layout reach the client as data attributes on ``<html>``, beside
    the theme and density the shell already reads from there. *base* is the URL
    prefix the router strips: ``/n/`` for the migration mount, ``/`` for the
    resource route, where the path already is the file path.
    """
    return Html(
        Head(
            Title(ROOT.name or "Filemill"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Meta(name="theme-color", content="#0770C9"),
            Link(rel="manifest", href="/manifest.json"),
            Link(rel="apple-touch-icon", href="/icons/icon-192.png"),
            Link(rel="stylesheet", href="/ui/core/styles.css"),
            Script(src="/ui/vendor/seti-map.js"),
        ),
        Body(
            *[Script(src=f"/ui/core/{n}") for n in _UI_CORE],
            *[
                Script(src=f"/ui/adapters/{n}", **_ui_script_attrs(n, base))
                for n in _UI_ADAPTERS
            ],
        ),
        lang="en",
        data_theme="light",
        data_density="compact",
        data_root=ROOT.name or "/",
        data_filemill=state.view,
        data_layout=state.layout,
    )


def _ui_script_attrs(name: str, base: str) -> dict:
    """Per-adapter configuration, read back via ``document.currentScript``."""
    if name == "http.js":
        return {"data_api": "/api"}
    if name == "router-path.js":
        return {"data_base": base}
    return {}


@rt(UI_BASE)
@rt(UI_BASE + "{path:path}")
def ui_view(path: str = ""):
    """Serve the shell for any path under the UI base.

    The path is validated but not otherwise used: the client walks down to it
    from the root, so a request for a file that has gone is a 404 here and a
    "the folder it was in" fallback there. Both are better than a blank page.

    Validation goes through ``split_vfs`` because ``/n/sample.db/users/42`` is a
    real file plus a key inside it — the joined form exists only in the URL.
    """
    if path and api.split_vfs(path, ROOT, _resolve_safe) is None:
        return HTMLResponse("Not found", status_code=404)
    return _ui_shell(urls.ViewState(), UI_BASE)


# ── JSON/fragment API behind the shared UI ───────────────────────────────────


def _api_target(p: str) -> Path | None:
    """Root-relative request path → a safe absolute path, or None."""
    candidate = api.rel_to_abs(p, ROOT)
    if candidate is None:
        return None
    return _resolve_safe(str(candidate))


@rt("/api/dir")
def api_dir(p: str = "", v: str = ""):
    """List a directory — or one level inside a virtual filesystem.

    ``v`` is the virtual path *within* the file named by ``p``. Keeping the two
    apart is what lets a `.db` be a directory of tables to the UI while staying
    one file to ``_resolve_safe``.
    """
    target = _api_target(p)
    if target is None:
        return JSONResponse({"entries": [], "denied": "Not found"}, status_code=404)
    if target.is_file():
        return api.vfs_dir_json(target, v)
    if not target.is_dir():
        return JSONResponse({"entries": [], "denied": "Not found"}, status_code=404)
    return api.dir_json(target)


@rt("/api/raw")
def api_raw(p: str = ""):
    """Serve a file's bytes."""
    target = _api_target(p)
    if target is None:
        return HTMLResponse("Not found", status_code=404)
    return api.raw_response(target)


@rt("/api/preview")
def api_preview(p: str = "", v: str = "", fmt: str = "", filemill: str = ""):
    """Render a preview body with the existing Python pipeline.

    ``filemill`` is the view from the page's own URL, forwarded by
    ui/adapters/preview-http.js. It picks the renderer and nothing else, so
    ``highlight`` means the same coloured source here as on the embedded page.
    """
    target = _api_target(p)
    if target is None:
        return HTMLResponse("", status_code=404)
    if v:
        return api.vfs_preview(target, v, fmt)
    render = render_source if filemill == urls.VIEW_HIGHLIGHT else render_preview
    return api.preview_fragment(target, render)


@rt("/api/render", methods=["POST"])
async def api_render(request):
    """Render posted bytes — the local-folder case, where the server has no path."""
    return await api.render_upload(request, render_preview)


# ── The root-relative resource route (PLAN-19) ───────────────────────────────
#
# Every route above this line is addressed by a prefix that names a *mechanism*:
# /click is an HTMX fragment, /w/ is a static mount, /api/ is JSON, /n/ is the
# shared UI. Those names are reserved and they win, so a directory in ROOT
# actually called "api" is not reachable under its own name. That is the one
# cost of putting files at the top level, and it is why the reserved set is
# written down here rather than discovered by a user hitting it.
#
# Everything else is addressed by the file's own path relative to ROOT. The
# resource and its representation are different things: /docs/readme.md names
# the file, and ?filemill= says which of its representations to send.

_RESOURCE_ROUTE = "/{path:path}"


def _rel_url_path(p: Path) -> str | None:
    """Return *p* as a ROOT-relative URL path, or None when it has no such path.

    Shares ``_mounted_path_parts`` with the ``/f/`` and ``/w/`` URL builders, so
    a bookmark symlink in ROOT keeps producing the visible path a reader expects
    (``bookmark/sub/file``) rather than the target's real location on disk.
    A standalone bookmark mount that is *not* reachable through the visible tree
    has no root-relative address at all, and says so with None.
    """
    mounted = _mounted_path_parts(p)
    if mounted is None:
        return None
    mount_name, rel = mounted
    if mount_name != ROOT.name:
        return None
    return rel.as_posix() if rel.parts else ""


def _resource_target(rel: str) -> tuple[Path, str, str] | None:
    """Root-relative URL path → (safe absolute path, real part, virtual part).

    ``sample.db/users/42`` is one URL naming two things: a file on disk and a key
    inside it. The split has to happen before resolution, because only the real
    part is a filesystem path — hence ``api.split_vfs`` rather than a plain join.

    Returns None when nothing safe is addressed. Every path still goes through
    ``_resolve_safe``, and the query never takes part in that decision.
    """
    split = api.split_vfs(rel, ROOT, _resolve_safe)
    if split is None:
        return None
    real_rel, vpath = split
    candidate = api.rel_to_abs(real_rel, ROOT)
    if candidate is None:
        return None
    target = _resolve_safe(str(candidate))
    if target is None or not target.exists():
        return None
    return target, real_rel, vpath


def _view_switch_html(rel: str, state) -> str:
    """Return the reciprocal representation controls (PLAN-19 §5).

    Every view links to every other view of the same path, so the controls are
    reciprocal by construction rather than by three hand-written bars. The stable
    hooks are the ``filemill-view-switch`` class and the ``data-filemill``
    attribute; the visible labels are not part of the contract.

    ``url_for_state`` carries the reader's layout and dotfile choices across the
    switch and HTML-escaping happens here, at the output boundary.
    """
    links = []
    for view, label in urls.VIEW_LABELS:
        href = html_lib.escape(urls.url_for_state(rel, state, view=view))
        active = " active" if view == state.view else ""
        current = ' aria-current="page"' if view == state.view else ""
        links.append(
            f'<a class="filemill-view-link{active}"'
            f' data-filemill="{view}" href="{href}"{current}>{label}</a>'
        )
    return (
        '<div class="preview-webmode-bar filemill-view-switch">'
        f"{''.join(links)}</div>"
    )


def _representation_html(target: Path, rel: str, state, vpath: str) -> str:
    """Render one representation of *target*, with the switch controls above it.

    Both branches reuse the existing pipelines rather than duplicating them:
    ``render_preview`` is the same function ``/click`` and ``/restore`` call, and
    ``render_source`` shares its Pygments and ``<pre>`` fallbacks.
    """
    if vpath:
        provider = REGISTRY.get(target)
        if provider is None:
            return '<div class="preview-error">Not a virtual filesystem</div>'
        try:
            body = provider.render_preview(
                target, vpath, provider.default_fmt(vpath), page=1, limit=1000
            )
        except Exception as exc:
            body = f'<div class="preview-error">{html_lib.escape(str(exc))}</div>'
        return _view_switch_html(rel, state) + body

    try:
        if state.view == urls.VIEW_HIGHLIGHT:
            body = render_source(target)
        else:
            # The state reaches the Markdown renderer so links inside the
            # document keep the reader's layout and dotfile choices.
            body = render_preview(target, state)
    except Exception as exc:
        body = f'<div class="preview-error">{html_lib.escape(str(exc))}</div>'
    return _view_switch_html(rel, state) + body


def _document_page(rel: str, state, body_html: str):
    """Return the ``layout=no-columns`` page: the representation and nothing else.

    This is what the gogo dashboard embeds. It carries no breadcrumb and no
    column rail, because the dashboard supplies its own chrome and two sets of
    navigation in one pane help nobody.
    """
    return _page_html(
        [Div(NotStr(body_html), id="preview", cls="preview-standalone")], state
    )


@rt(_RESOURCE_ROUTE, methods=["GET"])
def resource(request, path: str = ""):
    """Serve any representation of the file at ``ROOT / path``.

    The path names the resource; the query names the representation:

        /docs/readme.md                              the file's bytes
        /docs/readme.md?filemill=render     Markdown as HTML
        /docs/readme.md?filemill=highlight  the source, coloured
        /docs/readme.md?filemill=raw          the bytes, said out loud

    GET only. PLAN-19 §3 makes the router-facing surface read-only, and
    Filemill never writes a file under any route.
    """
    state = urls.parse_state(request.query_params)
    found = _resource_target(path)
    if found is None:
        # One 404 for "outside ROOT", "denied", and "missing" alike, so a probe
        # cannot learn from the status code whether an outside file exists.
        return HTMLResponse("Not found", status_code=404)
    target, rel, vpath = found
    vpath = vpath or state.vpath

    if target.is_dir():
        # A directory has no bytes, so every view value renders its listing. The
        # layout still applies: no-columns gives the one pane, and the column
        # layouts give the finder opened at that directory.
        if state.wants_columns:
            return _ui_shell(state, "/")
        return _page_html([list_column(target, ROOT, col_index=0)], state)

    if vpath:
        # A node inside a virtual filesystem has no bytes of its own, so `raw`
        # has nothing to serve there and the rendered view becomes the default.
        # This is the one place standalone and embedded diverge from "the bare
        # path serves bytes", and it diverges because there are no bytes.
        if state.view == urls.VIEW_RAW:
            state = state.with_view(urls.VIEW_RENDER)
    elif state.view == urls.VIEW_RAW:
        # Bytes, a detected media type, no HTML wrapper. This is what an <img
        # src> and a <link rel=stylesheet> need, and it is why raw is the
        # default: the bare path has to be the file itself.
        return api.raw_response(target)

    if state.wants_columns:
        # The columns are the shared UI's, not the HTMX shell's. The client
        # walks to this path and asks /api/preview for the representation, so
        # the document is not rendered twice.
        return _ui_shell(state, "/")
    return _document_page(rel, state, _representation_html(target, rel, state, vpath))


# ── PWA static files ─────────────────────────────────────────────────────────


@rt("/manifest.json")
def manifest():
    """Serve the Web App Manifest."""
    return FileResponse(
        str(_STATIC_DIR / "manifest.json"), media_type="application/manifest+json"
    )


@rt("/sw.js")
def service_worker():
    """Serve the service worker with the required Service-Worker-Allowed header."""
    data = (_STATIC_DIR / "sw.js").read_bytes()
    return Response(
        content=data,
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"},
    )


@rt("/icons/{name}")
def icon(name: str):
    """Serve a named icon from the bundled static/icons/ directory."""
    safe_name = Path(name).name  # strip any directory traversal
    icon_path = _STATIC_DIR / "icons" / safe_name
    if not icon_path.exists() or not icon_path.is_file():
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(str(icon_path))


# ── #38 CORS middleware (scoped to /w/) ──────────────────────────────────────

_CORS_HEADERS: dict[str, str] = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}


class _WebStaticCORSMiddleware(BaseHTTPMiddleware):
    """Add CORS headers to every /w/ response; handle OPTIONS preflight."""

    async def dispatch(self, request, call_next):
        if not request.url.path.startswith("/w/"):
            return await call_next(request)
        if request.method == "OPTIONS":
            return Response(status_code=200, headers=_CORS_HEADERS)
        response = await call_next(request)
        response.headers.update(_CORS_HEADERS)
        return response


app.add_middleware(_WebStaticCORSMiddleware)


# ── Route priority fix ────────────────────────────────────────────────────────
# FastHTML registers a catch-all /{fname:path}.{ext:static} at index 0 that
# intercepts any path with a known static extension (including .html, .txt, …)
# and serves it from the *working directory*. Move /w/ and /f/ in front of it so
# they are matched first.
#
# The root-relative resource route is a catch-all too, so ordering decides the
# whole contract and is stated in one place rather than left to registration
# order. Four bands, most specific first:
#
#   1. the named prefixes below            /w/, /f/, /api/, /n/, PWA files
#   2. every other explicitly named route  /click, /raw, /restore, /, …
#   3. /{path:path}                        the file's own path under ROOT
#   4. FastHTML's /{fname:path}.{ext:static}
#
# Band 3 answers before band 4, so a request for /notes/todo.txt now serves
# ROOT/notes/todo.txt rather than ./notes/todo.txt from the working directory.
# That is the point: the URL path is a path relative to the configured root.
def _reorder_routes() -> None:
    routes = app.router.routes
    _prefixes = {
        "/w/{path:path}",
        "/f/",
        "/f/{path:path}",
        "/manifest.json",
        "/sw.js",
        "/icons/{name}",
        # Without these, the catch-all eats every /ui/**.js and .css the shell
        # asks for and the new UI is a blank page.
        "/ui/{path:path}",
        UI_BASE,
        UI_BASE + "{path:path}",
        "/api/dir",
        "/api/raw",
        "/api/preview",
        "/api/render",
    }
    priority, rest, resource_route, static_fallback = [], [], [], []
    for r in routes:
        path = getattr(r, "path", "")
        if path == _RESOURCE_ROUTE:
            resource_route.append(r)
        elif "{ext:static}" in path:
            static_fallback.append(r)
        elif path in _prefixes:
            priority.append(r)
        else:
            rest.append(r)
    routes[:] = priority + rest + resource_route + static_fallback


_reorder_routes()
