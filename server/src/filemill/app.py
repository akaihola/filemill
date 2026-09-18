import json
import subprocess
from pathlib import Path
from urllib.parse import quote as urlquote

from fasthtml.common import (
    Body,
    Head,
    Html,
    Link,
    Meta,
    Script,
    Title,
    fast_app,
)
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)

from filemill import api, paths, pwa, urls
from filemill.env import env
from filemill.preview import render_preview, render_source

# HTML file extensions that get a "View as web page" button in the preview
_HTML_EXTS = {".html", ".htm"}

# Overridden by cli.py before serve() is called.
ROOT: Path = Path(env("ROOT", str(Path.home())))

app, rt = fast_app(
    hdrs=(),
    pico=False,
    live=False,
)


def _resolve(path_str: str) -> Path | None:
    """``paths.resolve_safe`` bound to the configured ROOT."""
    return paths.resolve_safe(path_str, ROOT)


@rt("/")
def index(request):
    """Serve the root directory; ``resource`` holds the one directory rule."""
    return resource(request)


# ── Named mounts ─────────────────────────────────────────────────────────────


@rt("/w/{path:path}")
def web_static(path: str):
    """Serve a named-mount ``/w/<mount>/...`` file with the correct Content-Type."""
    p = paths.resolve_web_mount(path, ROOT)
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
            Script(pwa.SW_REGISTER_JS),
        ),
        Body(Script(src=f"/ui/{_UI_ENTRY}", type="module")),
        lang="en",
        data_density="compact",
        data_root=ROOT.name or "/",
        data_absolute=ROOT.resolve().as_posix(),
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
    if path and api.split_vfs(path, ROOT, _resolve) is None:
        return HTMLResponse("Not found", status_code=404)
    return _ui_shell(urls.ViewState(), UI_BASE)


# ── JSON/fragment API behind the shared UI ───────────────────────────────────


def _api_target(p: str) -> Path | None:
    """Root-relative request path → a safe absolute path, or None."""
    candidate = api.rel_to_abs(p, ROOT)
    if candidate is None:
        return None
    return _resolve(str(candidate))


@rt("/api/dir")
def api_dir(p: str = "", v: str = "", page: int = 1):
    """List a directory — or one level inside a virtual filesystem.

    ``v`` is the virtual path *within* the file named by ``p``. Keeping the two
    apart is what lets a `.db` be a directory of tables to the UI while staying
    one file to ``paths.resolve_safe``.
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
        raw_url = f"/api/raw?p={urlquote(p, safe='/')}"
        render = lambda path: render_preview(path, preview_url=raw_url)
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
    if candidate is None or _resolve(str(candidate)) is None:
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


def _resource_target(rel: str) -> tuple[Path, str, str] | None:
    """Root-relative URL path → (safe absolute path, real part, virtual part).

    ``sample.db/users/42`` is one URL naming two things: a file on disk and a key
    inside it. The split has to happen before resolution, because only the real
    part is a filesystem path — hence ``api.split_vfs`` rather than a plain join.

    Returns None when nothing safe is addressed. Every path still goes through
    ``paths.resolve_safe``, and the query never takes part in that decision.
    """
    split = api.split_vfs(rel, ROOT, _resolve)
    if split is None:
        return None
    real_rel, vpath = split
    candidate = api.rel_to_abs(real_rel, ROOT)
    if candidate is None:
        return None
    target = _resolve(str(candidate))
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
        # A directory has no bytes, so every view value opens the shell on it.
        return _ui_shell(state, "/", request.query_params.get("hidden") == "show")

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
    return _ui_shell(state, "/", request.query_params.get("hidden") == "show")


# ── PWA static files ─────────────────────────────────────────────────────────

rt("/manifest.json")(pwa.manifest)
rt("/sw.js")(pwa.service_worker)
rt("/icons/{name}")(pwa.icon)


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
#   2. every other explicitly named route  /, …
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
