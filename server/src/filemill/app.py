import json
import os
import subprocess
from pathlib import Path
from textwrap import dedent
from urllib.parse import unquote as urlunquote

from fasthtml.common import (
    Body,
    Head,
    Html,
    Li,
    Link,
    Meta,
    Script,
    Style,
    Title,
    Ul,
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
from filemill.env import env
from filemill.preview import render_preview, render_source
from filemill.styles import APP_CSS

# CDN URL for mermaid.js (UMD build – sets window.mermaid on load)
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

# Overridden by cli.py before serve() is called.
ROOT: Path = Path(env("ROOT", str(Path.home())))

app, rt = fast_app(
    hdrs=(),
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
        Script(_SW_REGISTER_JS),
        *extra_head_scripts,
    )


def _plain_listing(path: Path) -> object:
    """Return a plain ``<ul>`` of one directory's entries, no interaction.

    ``layout=no-columns`` asks for the representation alone, so this list
    carries no click handlers or scripts — the shared UI is where navigation
    lives.
    """
    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        entries = []
    return Ul(*[Li(p.name + ("/" if p.is_dir() else "")) for p in entries])


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
def index(request):
    """Serve the root directory; ``resource`` holds the one directory rule."""
    return resource(request)


@rt("/raw")
def raw(path: str):
    """Serve raw file bytes (used by PDF iframe)."""
    p = _resolve_safe(path)
    if p is None or not p.is_file():
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(str(p))


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


# ── The shared Miller-columns UI ─────────────────────────────────────────────
#
# ui/ is the repository's shared frontend itself: the repo-root ../../../ui is
# a symlink to this directory, so there is one set of files and no copy to keep
# in step. It lives inside the package because a wheel cannot reach outside
# itself at runtime — see ui/adapters/README.md. The static edition builds its
# single file from these same sources, which is what makes these the same app
# rather than two that resemble each other. Its core/ is source-agnostic; the
# adapters ui/entry-server.js names point it at this server.
#
# Mounted under /n/ during the migration. Cutting over is changing UI_BASE to
# "/" and letting the catch-all serve the shell — at which point the URL path
# *is* the file path relative to ROOT, with no prefix at all.

UI_BASE = "/n/"
_UI_DIR: Path = Path(__file__).parent / "ui"

# The shell loads one module, ui/entry-server.js, which imports the core and
# this edition's adapters in dependency order. Both filesystem adapters are in
# that graph because "Open local folder…" switches between them at runtime;
# app-http.js is what selects. The static edition's entry-static.js names the
# other set — see ui/adapters/README.md.
_UI_ENTRY = "entry-server.js"


@rt("/ui/{path:path}")
def ui_asset(path: str):
    """Serve a vendored UI file."""
    parts = [p for p in path.split("/") if p not in ("", ".", "..")]
    target = _UI_DIR.joinpath(*parts)
    if not parts or not target.is_file():
        return HTMLResponse("Not found", status_code=404)
    media = {
        ".js": "application/javascript",
        ".css": "text/css",
        ".woff": "font/woff",
    }.get(target.suffix, "application/octet-stream")
    return FileResponse(str(target), media_type=media)


# The commit the settings menu shows beside the version. Asked of the package
# directory's repository once at import: a development checkout has one, an
# installed wheel does not — then the attribute is omitted and the menu shows
# the version alone, exactly like the static build.
try:
    _COMMIT = subprocess.run(
        ["git", "-C", str(Path(__file__).parent), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
except OSError:
    _COMMIT = ""


# ui/adapters/preview-rich.js imports its renderers from the URL FILEMILL_CDN
# names, or from a CDN when it names none. This edition serves the Markdown and
# .docx modules itself — ui/vendor/README.md lists the pins — so a document
# renders with nothing fetched from a third party, and the rich-preview switch
# does not apply to them. reStructuredText stays with Python; .pptx keeps its
# CDN viewer.
_VENDOR_MAP_JS = (
    "window.FILEMILL_CDN = "
    + json.dumps(
        {
            name: f"/ui/vendor/{name}.js"
            for name in (
                "markdown-it",
                "markdown-it-footnote",
                "markdown-it-deflist",
                "markdown-it-task-lists",
                "markdown-it-anchor",
                "mammoth",
            )
        }
    )
    + ";"
)


def _ui_shell(state, base: str, hidden: bool = False):
    """The app shell for the shared UI. Deliberately almost empty.

    The chrome is built by ui/core/shell.js so that this page and filemill's
    index.html cannot drift apart — there is no markup here to keep in step.

    The view and layout reach the client as data attributes on ``<html>``, beside
    the theme and density the shell already reads from there, and so do the two
    adapter settings: the API prefix for ui/adapters/http.js and *base*, the URL
    prefix ui/adapters/router-path.js strips — ``/n/`` for the migration mount,
    ``/`` for the resource route, where the path already is the file path.
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
            Script(_VENDOR_MAP_JS),
            Script(_SW_REGISTER_JS),
        ),
        Body(Script(src=f"/ui/{_UI_ENTRY}", type="module")),
        lang="en",
        data_density="compact",
        data_root=ROOT.name or "/",
        data_api="/api",
        data_base=base,
        data_filemill=state.view,
        data_layout=state.layout,
        **({"data_commit": _COMMIT} if _COMMIT else {}),
        **({"data_hidden": "show"} if hidden else {}),
    )


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
def api_dir(p: str = "", v: str = "", page: int = 1):
    """List a directory — or one level inside a virtual filesystem.

    ``v`` is the virtual path *within* the file named by ``p``. Keeping the two
    apart is what lets a `.db` be a directory of tables to the UI while staying
    one file to ``_resolve_safe``.
    """
    if page < 1:
        return JSONResponse({"entries": [], "denied": "Invalid page"}, status_code=400)
    target = _api_target(p)
    if target is None:
        return JSONResponse({"entries": [], "denied": "Not found"}, status_code=404)
    if target.is_file():
        return api.vfs_dir_json(target, v, page)
    if not target.is_dir():
        return JSONResponse({"entries": [], "denied": "Not found"}, status_code=404)
    return api.dir_json(target, page)


@rt("/api/search")
def api_search(q: str = "", p: str = ""):
    """Search file contents below ROOT with the bounded ripgrep operation."""
    try:
        focused = _api_target(p)
        if focused is None or not focused.is_dir():
            return JSONResponse({"error": "Not found"}, status_code=404)
        return JSONResponse({"matches": api.search_root(ROOT, q, p)})
    except api.SearchError as exc:
        status = 400 if "query" in str(exc).lower() else 503
        return JSONResponse({"error": str(exc)}, status_code=status)


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
    if filemill == urls.VIEW_HIGHLIGHT:
        render = render_source
    elif target.suffix.lower() == ".vtt":
        return api.vfs_preview(target, "", fmt)
    else:
        render = lambda path: render_preview(path, preview_url=urls.build_url(p))
    return api.preview_fragment(target, render)


@rt("/api/save", methods=["POST"])
async def api_save(request, p: str = ""):
    """Overwrite a text file — the preview pane's Edit → Save."""
    target = _api_target(p)
    if target is None:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return api.save_file(target, await request.body())


@rt("/api/delete", methods=["DELETE"])
def api_delete(p: str = ""):
    """Delete one real file or directory after the normal root check."""
    candidate = api.rel_to_abs(p, ROOT)
    if candidate is None or _resolve_safe(str(candidate)) is None:
        return JSONResponse({"error": "Not found"}, status_code=404)
    if candidate.resolve() == ROOT.resolve():
        return JSONResponse({"error": "Not found"}, status_code=404)
    return api.delete_file(candidate)


# ── The root-relative resource route (PLAN-19) ───────────────────────────────
#
# Every route above this line is addressed by a prefix that names a *mechanism*:
# /w/ is a static mount, /api/ is JSON, /n/ is the shared UI. Those names are
# reserved and they win, so a directory in ROOT
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


@rt(_RESOURCE_ROUTE, methods=["GET"])
def resource(request, path: str = ""):
    """Serve any representation of the file at ``ROOT / path``.

    The path names the resource; the query names the representation:

        /docs/readme.md                              the file's bytes
        /docs/readme.md?filemill=render     Markdown as HTML
        /docs/readme.md?filemill=highlight  the source, coloured
        /docs/readme.md?filemill=raw          the bytes, said out loud
        /docs/readme.md/                     redirects to filemill=render

    GET only. PLAN-19 §3 makes the router-facing surface read-only, and
    Filemill never writes a file under any route.
    """
    state = urls.parse_state(request.query_params)
    found = _resource_target(path)
    if found is None:
        # One 404 for "outside ROOT", "denied", and "missing" alike, so a probe
        # cannot learn from the status code whether an outside file exists.
        return HTMLResponse("Not found", status_code=404)
    target, _rel, vpath = found
    vpath = vpath or state.vpath

    if (
        path.endswith("/")
        and not target.is_dir()
        and urls.VIEW_PARAM not in request.query_params
        and urls.VIEW_SHORT_PARAM not in request.query_params
    ):
        canonical = urls.build_url(path, view=urls.VIEW_RENDER)
        if request.url.query:
            canonical += "&" + request.url.query
        return RedirectResponse(canonical, status_code=302)

    if target.is_dir():
        # A bare directory URL is a web address first: if the directory holds an
        # index.html, that file is the answer, served as-is. Any query at all is
        # a request for Filemill, so it falls through to the listing.
        index_file = target / "index.html"
        if not request.query_params and index_file.is_file():
            return FileResponse(str(index_file), media_type="text/html")
        # A directory has no bytes, so every view value renders its listing.
        if state.wants_columns:
            return _ui_shell(state, "/", request.query_params.get("hidden") == "show")
        return _page_html([_plain_listing(target)], state)

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
        # The client walks to this path and asks /api/preview for the
        # representation, so the document is not rendered twice.
        return _ui_shell(state, "/", request.query_params.get("hidden") == "show")
    return _ui_shell(state, "/", request.query_params.get("hidden") == "show")


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
# and serves it from the *working directory*. Move /w/ in front of it so
# it is matched first.
#
# The root-relative resource route is a catch-all too, so ordering decides the
# whole contract and is stated in one place rather than left to registration
# order. Four bands, most specific first:
#
#   1. the named prefixes below            /w/, /api/, /n/, PWA files
#   2. every other explicitly named route  /raw, /, …
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
        "/api/save",
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
