# Contributing to pykofinder

## Project context

pykofinder is a **macOS Finder-style column-view file browser and previewer**,
served as a FastHTML web application. Directories are navigated by clicking
column entries; files are previewed inline (Markdown, DOCX, PPTX, PDF, images,
plain text, code with syntax highlighting).

### Source layout

```
src/pykofinder/
├── app.py          # FastHTML app, routes, _resolve_safe()
├── api.py          # JSON/fragment API behind the shared UI (/api/*)
├── cli.py          # Typer CLI entry point
├── columns.py      # Column HTML generation + breadcrumb + pruning JS  (old UI)
├── preview.py      # Preview dispatcher (md / docx / pptx / pdf / img / code / raw)
├── rendering.py    # markdown-it-py instance with plugins
├── styles.py       # CSS + Pygments theme + HTMX + keyboard + live-reload JS
├── vfs.py          # Virtual-filesystem registry + provider protocol
├── providers/      # VFS backends (SQLite, JSON, CSV)
├── static/         # Bundled PWA assets (manifest.json, sw.js, icons/)
└── ui/             # VENDORED — filemill's frontend; see "The shared UI" below

tests/
├── conftest.py               # Shared fixtures (tmp dirs, test client)
├── test_api.py               # /api/* contract + the shared UI's shell
├── test_app.py               # Route-level integration tests
├── test_browser_new_ui.py    # The shared UI, driven in a real browser
├── test_cli.py               # CLI smoke tests
├── test_columns.py           # Column HTML generation + breadcrumb
├── test_integration_vfs.py   # End-to-end VFS navigation tests
├── test_preview.py           # Preview rendering (all file types)
├── test_providers_sqlite.py  # SQLite VFS provider unit tests
├── test_pwa.py               # PWA assets (manifest, SW, icons, head tags)
├── test_rendering.py         # Markdown pipeline + selected-state CSS/JS
├── test_resolve_safe.py      # Path-safety logic (_resolve_safe)
├── test_routes_new.py        # Additional route coverage
└── test_vfs.py               # VFS registry and provider protocol
```

### The shared UI

`src/pykofinder/ui/` is **a verbatim copy of filemill's frontend**, not a fork.
filemill and pykofinder show the same application; the only difference is which
adapters the shared `core/` is handed:

| | filemill | pykofinder |
| --- | --- | --- |
| filesystem | File System Access API | `GET /api/dir` |
| preview | text/image, in the browser | `GET /api/preview` — **this module's renderers** |
| router | `#r=root&p=a/b.md` | `/n/a/b.md` |

That is why `preview.py`, `rendering.py`, `vfs.py` and `providers/` never had to
be rewritten in JavaScript, and why `POST /api/render` exists: when the browser
opens a *local* folder the server cannot read it, so the bytes are posted and
come back through the same markdown-it-py/Pygments/mammoth pipeline.

**Never edit anything under `ui/`.** Change it in filemill, then:

```bash
tools/sync-ui.py [path/to/filemill]   # re-vendor
tools/sync-ui.py --check              # exits 1 if the copy is stale
```

The copy keeps filemill's directory shape (`ui/src/{core,adapters}` beside
`ui/vendor`) because `styles.css` reaches the icon font as
`../../vendor/seti.woff` — flattening a level 404s it. `ui/src/adapters/README.md`
documents the three ports.

The new UI is mounted at `UI_BASE = "/n/"` while the HTMX UI at `/f/` is still
the default. Cutting over means pointing `UI_BASE` at `/`, after which the URL
path *is* the file path relative to ROOT, with no prefix.

### Key invariants

- All routes are under a configurable `ROOT` directory; `_resolve_safe()` in
  `app.py` enforces that no path escapes that root (symlinks included).
- Static `/w/` URLs use named mounts: the root directory is exposed as
  `/w/<ROOT.name>/...`, and each direct symlink child of ROOT is exposed as
  `/w/<symlink-name>/...`.
- Column pruning is done client-side via a small `<script>` injected into each
  click response – no server round-trip needed.
- HTMX drives all dynamic updates in the `/f/` UI; there is no JavaScript build
  step in either UI.
- Every path in the `/api/*` and `/n/` routes is **relative to ROOT**; absolute
  paths are refused outright (`api.rel_to_abs`), because `ROOT / "/etc/passwd"`
  is `/etc/passwd`. Containment is still checked afterwards by `_resolve_safe()`.
- The shared UI fetches nothing from a network: every asset it needs is served
  from `ui/`. The `/f/` UI's htmx and mermaid CDN tags are why its browser tests
  cannot run offline.
- Client-side keyboard navigation must keep the browser URL in sync with the visible Finder state; if a key handler changes columns/preview without an HTMX request, it must update history explicitly.
- PWA static assets (`/manifest.json`, `/sw.js`, `/icons/*`) are served from
  `src/pykofinder/static/` and are bundled with the package; they are
  prioritised above FastHTML's static catch-all route in `_reorder_routes()`.
  So are `/ui/`, `/n/` and `/api/*` — without that, the catch-all swallows every
  `.js` and `.css` the shared UI asks for and it renders as a blank page.

---

## Development rules

- **TDD (red-green)** – write a failing test first, then make it pass; never
  write production code without a failing test driving it.
- **Full test coverage** – every new or changed behaviour must be covered by
  tests; the suite runs at 100% branch coverage. Unit/integration tests use
  pytest.
- **Documentation stays current** – update `README.md`, `ISSUES.md`, and
  `TASKS.md` as part of every change, not as an afterthought.
- **Simplify aggressively** – look for opportunities to simplify and gain
  elegance on every pass; less code is usually better code.
- **Frequent conventional commits** – commit at every logical checkpoint using
  the conventional-commit prefixes: `feat:`, `fix:`, `test:`, `docs:`,
  `refactor:`, `chore:`, `style:`, `perf:`.

## Running tests

```bash
uv sync
uv run pytest                  # unit + integration (with coverage)

# Real-browser regression tests (optional; requires PLAYWRIGHT_BROWSERS_PATH)
# Keep browser regressions here for keyboard URL sync and keyboard-only column-survival flows.
PLAYWRIGHT_BROWSERS_PATH="$PLAYWRIGHT_BROWSERS_PATH" \
  uv run --with "playwright==1.57.0" pytest tests/test_browser_keyboard.py
```

> **Important:** always wrap `uv run pytest` in a shell-level timeout (e.g.
> `timeout 120 uv run pytest`) when calling it from a script or agent tool.
> SSE streaming tests that misbehave can otherwise block indefinitely (see
> [issue #17](ISSUES.md#17--fix-hanging-sse-test-test_sse_reload_exists_with_live_mode)).

## Submitting changes

1. Open an issue in `ISSUES.md` and set its status to `in-progress`.
2. Add a matching `[~]` entry in `TASKS.md`.
3. Follow the TDD cycle above.
4. Update `README.md`, `CONTRIBUTING.md`, `ISSUES.md`, and `TASKS.md`.
5. Mark the issue closed before committing.
