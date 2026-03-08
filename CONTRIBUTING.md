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
├── cli.py          # Typer CLI entry point
├── columns.py      # Column HTML generation + breadcrumb + pruning JS
├── preview.py      # Preview dispatcher (md / docx / pptx / pdf / img / code / raw)
├── rendering.py    # markdown-it-py instance with plugins
├── styles.py       # CSS + Pygments theme + HTMX + keyboard + live-reload JS
├── vfs.py          # Virtual-filesystem registry + provider protocol
├── providers/      # VFS backends (SQLite, JSON, CSV)
└── static/         # Bundled PWA assets (manifest.json, sw.js, icons/)

tests/
├── conftest.py               # Shared fixtures (tmp dirs, test client)
├── test_app.py               # Route-level integration tests
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

### Key invariants

- All routes are under a configurable `ROOT` directory; `_resolve_safe()` in
  `app.py` enforces that no path escapes that root (symlinks included).
- Static `/w/` URLs use named mounts: the root directory is exposed as
  `/w/<ROOT.name>/...`, and each direct symlink child of ROOT is exposed as
  `/w/<symlink-name>/...`.
- Column pruning is done client-side via a small `<script>` injected into each
  click response – no server round-trip needed.
- HTMX drives all dynamic updates; there is no JavaScript build step.
- Client-side keyboard navigation must keep the browser URL in sync with the visible Finder state; if a key handler changes columns/preview without an HTMX request, it must update history explicitly.
- PWA static assets (`/manifest.json`, `/sw.js`, `/icons/*`) are served from
  `src/pykofinder/static/` and are bundled with the package; they are
  prioritised above FastHTML's static catch-all route in `_reorder_routes()`.

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
