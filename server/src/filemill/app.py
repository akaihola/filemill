import hashlib
import inspect
import json
import re
import secrets
import subprocess
from html import escape
from pathlib import Path
from urllib.parse import urlencode

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from starlette.routing import Route

from filemill import api, mutations, paths, pwa, urls
from filemill.env import env, env_flag
from filemill.preview import render_preview

# Unused since the HTMX finder and its "View as web page" button were removed.
_HTML_EXTS = {".html", ".htm"}

# Used when app.state.root is unset: direct ASGI loading, and cli.py --live,
# which passes its resolved root through FILEMILL_ROOT.
ROOT: Path = Path(env("ROOT", str(Path.home())))

app = Starlette()
app.state.root = None
# A public instance never lists or serves a hidden path (ADR 0087). cli.py sets
# this from --public; direct ASGI loading and --live read FILEMILL_PUBLIC.
app.state.public = env_flag("PUBLIC")
app.state.mutation_token = secrets.token_urlsafe(32)


class HostMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and not mutations.host_allowed(Request(scope)):
            response = JSONResponse({"error": "Forbidden"}, status_code=403)
            await response(scope, receive, send)
        else:
            await self.app(scope, receive, send)


app.add_middleware(HostMiddleware)


def rt(path: str, methods: list[str] | None = None):
    def register(endpoint):
        parameters = inspect.signature(endpoint).parameters

        async def dispatch(request):
            values = {}
            for name, parameter in parameters.items():
                if name == "request":
                    values[name] = request
                elif name in request.path_params:
                    values[name] = request.path_params[name]
                elif name in request.query_params:
                    value = request.query_params[name]
                    if parameter.annotation is int:
                        value = int(value)
                    values[name] = value
            if inspect.iscoroutinefunction(endpoint):
                return await endpoint(**values)
            return await run_in_threadpool(endpoint, **values)

        app.router.routes.append(Route(path, dispatch, methods=methods or ["GET"]))
        return endpoint

    return register


def _resolve(path_str: str, zones=None) -> Path | None:
    """``paths.resolve_safe`` bound to the configured ROOT and mode."""
    return paths.resolve_safe(path_str, _root(), zones, public=app.state.public)


def _hidden(*rels: str) -> bool:
    """True on a public instance when a request path names a hidden component.

    Checked before resolution, because a hidden name can lead to a visible
    path, and answering would confirm that the hidden name exists.
    """
    return app.state.public and any(paths.hidden(rel) for rel in rels)


def _zones(request):
    if not hasattr(request.state, "path_zones"):
        request.state.path_zones = paths.symlink_zones(_root())
    return request.state.path_zones


def _root() -> Path:
    return app.state.root or ROOT


@rt("/")
def index(request):
    """Serve the root directory; ``resource`` holds the one directory rule."""
    return resource(request)


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
# The resource route below serves the shell at each file's own path, with base
# "/", so the URL path *is* the file path relative to ROOT.
_UI_DIR: Path = Path(__file__).parent / "ui"

# The shell loads one module, ui/entry-server.js, which imports the core and
# this edition's adapters in dependency order. Both filesystem adapters are in
# that graph because "Open Folder…" switches between them at runtime;
# app-http.js is what selects. The static edition's entry-static.js names the
# other set — see ui/adapters/README.md.
_UI_ENTRY = "entry-server.js"
# Version the complete import graph so a CDN cannot mix releases.
_UI_ASSETS = {
    f"/ui/{path.relative_to(_UI_DIR).as_posix()}": (
        f"/ui/{path.relative_to(_UI_DIR).as_posix()}"
        f"?v={hashlib.sha256(path.read_bytes()).hexdigest()[:12]}"
    )
    for path in sorted(_UI_DIR.rglob("*"))
    if path.is_file() and path.suffix in {".js", ".css"}
}
_UI_IMPORTS = json.dumps(
    {"imports": {path: url for path, url in _UI_ASSETS.items() if path.endswith(".js")}}
)


@rt("/ui/{path:path}")
def ui_asset(path: str):
    """Serve a shared UI module or asset, including ui/vendor/."""
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
# does not apply to them. reStructuredText stays with Python. .pptx needs no
# module: preview-rich.js extracts its slide text in the browser.
_VENDOR_MAP_JS = (
    "window.FILEMILL_CDN = "
    + json.dumps(
        {
            name: _UI_ASSETS[f"/ui/vendor/{name}.js"]
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


def _ui_shell(state, hidden: bool = False):
    """The app shell for the shared UI. Deliberately almost empty.

    The chrome is built by ui/core/shell.js so that this page and filemill's
    index.html cannot drift apart — there is no markup here to keep in step.

    The view and layout reach the client as data attributes on ``<html>``, beside
    the theme and density the shell already reads from there, and so do the two
    adapter settings: the API prefix for ui/adapters/http.js and the root URL
    base for ui/adapters/router-path.js.
    """
    # The shell always renders, so a raw request here is a rendered one. The
    # client's view toggle trusts this attribute; "raw" would mislabel it.
    if state.view == urls.VIEW_RAW:
        state = state.with_view(urls.VIEW_RENDER)
    attrs = {
        "lang": "en",
        "data-density": "compact",
        "data-root": _root().name or "/",
        "data-absolute": _root().resolve().as_posix(),
        "data-api": "/api",
        "data-base": "/",
        "data-filemill": state.view,
        "data-layout": state.layout,
    }
    if not app.state.public:
        attrs["data-mutation-token"] = app.state.mutation_token
    if _COMMIT:
        attrs["data-commit"] = _COMMIT
    if hidden and not app.state.public:
        attrs["data-hidden"] = "show"
    attr_text = " ".join(
        f'{key}="{escape(str(value), quote=True)}"' for key, value in attrs.items()
    )
    title = escape(_root().name or "Filemill")
    return HTMLResponse(
        f'''<!doctype html>
<html {attr_text}><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0770C9">
<link rel="manifest" href="/manifest.json"><link rel="apple-touch-icon" href="/icons/icon-192.png">
<link rel="stylesheet" href="{_UI_ASSETS["/ui/core/styles.css"]}"><script src="{_UI_ASSETS["/ui/vendor/seti-map.js"]}"></script>
<script type="importmap">{_UI_IMPORTS}</script>
<script>{_VENDOR_MAP_JS}</script><script>{pwa.SW_REGISTER_JS}</script><title>{title}</title>
</head><body><script src="{_UI_ASSETS[f"/ui/{_UI_ENTRY}"]}" type="module"></script></body></html>''',
        # The service worker keeps an offline copy of a page only when this
        # header says it is the shell (static/sw.js, ADR 0089).
        headers={"Cache-Control": "no-store", "X-Filemill-Shell": "1"},
    )


# ── JSON/fragment API behind the shared UI ───────────────────────────────────


def _api_target(p: str, zones=None, v: str = "") -> Path | None:
    """Root-relative request path → a safe absolute path, or None.

    *v*, a virtual path inside the file, only takes part in the hidden check.
    """
    if _hidden(p, v):
        return None
    candidate = api.rel_to_abs(p, _root())
    if candidate is None:
        return None
    return _resolve(str(candidate), zones)


def _listed(zones):
    """A public listing keeps only the entries the instance would serve."""
    zones = paths.public_zones(_root(), zones)

    def keep(child: Path) -> bool:
        try:
            return not child.name.startswith(".") and paths.visible(
                child.resolve(), zones
            )
        except (OSError, RuntimeError):
            return False

    return keep


@rt("/api/dir")
def api_dir(request, p: str = "", v: str = ""):
    """List a directory — or one level inside a virtual filesystem.

    ``v`` is the virtual path *within* the file named by ``p``. Keeping the two
    apart is what lets a `.db` be a directory of tables to the UI while staying
    one file to ``paths.resolve_safe``.
    """
    zones = _zones(request)
    target = _api_target(p, zones, v)
    if target is None:
        return JSONResponse({"entries": [], "denied": "Not found"}, status_code=404)
    public = app.state.public
    if target.is_file():
        return api.vfs_dir_json(
            target,
            v,
            keep=(lambda vpath: not paths.dotted(vpath.split("/"))) if public else None,
        )
    if not target.is_dir():
        return JSONResponse({"entries": [], "denied": "Not found"}, status_code=404)
    return api.dir_json(target, keep=_listed(zones) if public else None)


@rt("/api/search")
def api_search(request, q: str = "", p: str = ""):
    """Search file contents below ROOT with the bounded ripgrep operation."""
    try:
        zones = _zones(request)
        focused = _api_target(p, zones)
        if focused is None or not focused.is_dir():
            return JSONResponse({"error": "Not found"}, status_code=404)
        matches = api.search_root(_root(), q, p)
        if app.state.public:
            # ripgrep skips hidden files by default; a user's ripgrep config
            # could change that, so drop what the instance would not serve.
            matches = [m for m in matches if _api_target(m["path"], zones)]
        return JSONResponse({"matches": matches})
    except api.SearchError as exc:
        status = 400 if "query" in str(exc).lower() else 503
        return JSONResponse({"error": str(exc)}, status_code=status)


@rt("/api/raw")
def api_raw(request, p: str = "", v: str = ""):
    """Serve a file's bytes — or, with ``v``, one member's bytes from inside it."""
    target = _api_target(p, _zones(request), v)
    if target is None:
        return HTMLResponse("Not found", status_code=404)
    if v:
        if not target.is_file():
            return HTMLResponse("Not found", status_code=404)
        return api.member_raw_response(target, v)
    return api.raw_response(target)


@rt("/api/preview")
def api_preview(request, p: str = "", lines: str = "", v: str = ""):
    """Render a file — or, with ``lines=START-END``, one slice of its lines.

    The slice is 0-based and end-exclusive, the way the browser's heading
    outline (``ui/core/model/headings.js``) spans a section. Only the
    reStructuredText renderer reads it; every other kind renders whole.

    With ``v``, the file is an archive and the member at that virtual path is
    what renders, as the file it is.
    """
    target = _api_target(p, _zones(request), v)
    if target is None or not target.is_file():
        return HTMLResponse("Not found", status_code=404)
    if v:
        raw = "/api/raw?" + urlencode({"p": p, "v": v})
        return api.member_preview_response(target, v, escape(raw, quote=True))
    span = None
    if lines:
        match = re.fullmatch(r"(\d+)-(\d+)", lines)
        if match is None:
            return HTMLResponse("Bad lines", status_code=400)
        span = (int(match[1]), int(match[2]))
    return HTMLResponse(
        render_preview(
            target, preview_url=escape(urls.build_url(p), quote=True), lines=span
        ),
        headers={"Cache-Control": "no-store"},
    )


@rt("/api/save", methods=["POST"])
async def api_save(request, p: str = ""):
    """Overwrite a text file — the preview pane's Edit → Save."""
    if not mutations.authorized(request):
        return JSONResponse({"error": "Forbidden"}, status_code=403)
    target = _api_target(p, _zones(request))
    if target is None:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return api.save_file(target, await request.body())


@rt("/api/delete", methods=["DELETE"])
def api_delete(request, p: str = ""):
    """Delete one real file or directory after authorization and the root check."""
    if not mutations.authorized(request):
        return JSONResponse({"error": "Forbidden"}, status_code=403)
    candidate = api.rel_to_abs(p, _root())
    if (
        _hidden(p)
        or candidate is None
        or _resolve(str(candidate), _zones(request)) is None
    ):
        return JSONResponse({"error": "Not found"}, status_code=404)
    if candidate.resolve() == _root().resolve():
        return JSONResponse({"error": "Not found"}, status_code=404)
    return api.delete_file(candidate)


# ── The root-relative resource route ─────────────────────────────────────────
#
# Explicit API, UI-asset and PWA routes take priority over resource paths.
# Only their registered patterns win; other paths use the resource route.
#
# Everything else is addressed by the file's own path relative to ROOT. The
# resource and its representation are different things: /docs/readme.md names
# the file, and ?filemill= says which of its representations to send.

_RESOURCE_ROUTE = "/{path:path}"


def _resource_target(rel: str, zones=None) -> tuple[Path, str, str] | None:
    """Root-relative URL path → (safe absolute path, real part, virtual part).

    ``sample.db/users/42`` is one URL naming two things: a file on disk and a key
    inside it. The split has to happen before resolution, because only the real
    part is a filesystem path — hence ``api.split_vfs`` rather than a plain join.

    Returns None when nothing safe is addressed. Every path still goes through
    ``paths.resolve_safe``, and the query never takes part in that decision.
    """
    if _hidden(rel):
        return None
    zones = zones or paths.symlink_zones(_root())
    split = api.split_vfs(rel, _root(), lambda p: _resolve(p, zones))
    if split is None:
        return None
    real_rel, vpath = split
    candidate = api.rel_to_abs(real_rel, _root())
    if candidate is None:
        return None
    target = _resolve(str(candidate), zones)
    if target is None or not target.exists():
        return None
    return target, real_rel, vpath


@rt(_RESOURCE_ROUTE, methods=["GET"])
def resource(request, path: str = ""):
    """Serve any representation of the file at ``ROOT / path``.

    The path names the resource; the query names the representation:

        /docs/readme.md                              the file's bytes
        /docs/readme.md?filemill=raw        the bytes, said out loud
        /docs/readme.md?filemill=render     the shell; the client renders it
        /docs/readme.md?filemill=highlight  the shell; the client shows source
        /docs/readme.md/                    redirects to filemill=render

    GET only. The router-facing surface is read-only, and mutation routes are
    authorized separately.
    """
    state = urls.parse_state(request.query_params)
    found = _resource_target(path, _zones(request))
    if found is None or _hidden(state.vpath):
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
        #
        # A public instance treats an index it would not serve as absent, so
        # the answer says nothing about a hidden target (ADR 0087).
        index_file = target / "index.html"
        if not request.query_params and (app.state.public or index_file.is_file()):
            resolved_index = _resolve(str(index_file), _zones(request))
            if resolved_index is not None and resolved_index.is_file():
                return FileResponse(str(resolved_index), media_type="text/html")
            if not app.state.public:
                return HTMLResponse("Not found", status_code=404)
        # A directory has no bytes, so every view value opens the shell on it.
        return _ui_shell(state, request.query_params.get("hidden") == "show")

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

    # Every other view is the shell. The client reads data-filemill and
    # data-layout from <html> and renders the document itself.
    return _ui_shell(state, request.query_params.get("hidden") == "show")


# ── PWA static files ─────────────────────────────────────────────────────────

rt("/manifest.json")(pwa.manifest)
rt("/sw.js")(pwa.service_worker)
rt("/icons/{name}")(pwa.icon)


# ── Route priority fix ────────────────────────────────────────────────────────
# A catch-all route for known static extensions would intercept resource paths
# and serve them from the working directory. Keep the explicit routes first.
#
# The root-relative resource route is a catch-all too, so ordering decides the
# whole contract and is stated in one place rather than left to registration
# order. Four bands, most specific first:
#
#   1. the named prefixes below            /api/, /ui/, PWA files
#   2. every other explicitly named route  /, …
#   3. /{path:path}                        the file's own path under ROOT
#   4. any static fallback
#
# Band 3 answers before band 4, so a request for /notes/todo.txt now serves
# ROOT/notes/todo.txt rather than ./notes/todo.txt from the working directory.
# That is the point: the URL path is a path relative to the configured root.
def _reorder_routes() -> None:
    routes = app.router.routes
    _prefixes = {
        "/manifest.json",
        "/sw.js",
        "/icons/{name}",
        # Without these, the catch-all eats every /ui/**.js and .css the shell
        # asks for and the new UI is a blank page.
        "/ui/{path:path}",
        "/api/dir",
        "/api/raw",
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
