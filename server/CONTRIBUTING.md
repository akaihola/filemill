# Contributing to Filemill — server edition

## Project context

filemill is a **macOS Finder-style column-view file browser and previewer**,
served as a FastHTML web application. Directories are navigated by clicking
column entries; files are previewed inline (Markdown, DOCX, PPTX, PDF, images,
plain text, code with syntax highlighting).

### Source layout

```
src/filemill/
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

The frontend lives at **`../ui/`**, the repository root's shared directory. The
static edition builds its single-file bundle from it and this package serves it,
so the two are the same application — not two that resemble each other. The only
difference is which adapters the shared `core/` is handed:

| | **static** | **server** (here) |
| --- | --- | --- |
| filesystem | File System Access API | `GET /api/dir` |
| preview | text/image, in the browser | `GET /api/preview` — **this module's renderers** |
| router | `#r=root&p=a/b.md` | `/n/a/b.md` |

Virtual filesystems ride through the same adapter. A `.db` is listed as a
directory (only when its provider actually yields entries — the CSV stub stays a
file), and its children carry a **`vpath`**: a path *inside* the file. An entry
with a `vpath` keeps its parent's real path and descends virtually; one without
joins its name on. The server decides which by putting a `vpath` on the entries
it returns, so `ui/src/core/` never learns that virtual nodes exist.

`/n/sample.db/users/1` is therefore one URL naming two things. `api.split_vfs()`
separates them, and is what a deep link is validated through — the joined form
exists only in the address bar.

That is why `preview.py`, `rendering.py`, `vfs.py` and `providers/` never had to
be rewritten in JavaScript, and why `POST /api/render` exists: when the browser
opens a *local* folder the server cannot read it, so the bytes are posted and
come back through the same markdown-it-py/Pygments/mammoth pipeline.

**Never edit anything under `src/filemill/ui/`.** That is a copy of `../ui/`,
made so a wheel is self-contained — a package cannot reach outside itself at
runtime. Edit `../ui/`, then:

```bash
tools/sync-ui.py            # refresh the packaged copy from ../ui
tools/sync-ui.py --check    # exits 1 if it is stale; CI runs this
```

Because it is one repository, a UI change lands in both projects in one commit;
the copy is a packaging step, not a synchronisation problem.
`../ui/adapters/README.md` documents the three ports.

The shared UI is mounted at `UI_BASE = "/n/"` while the HTMX UI at `/f/` is
still the default. Cutting over means pointing `UI_BASE` at `/`, after which the URL
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
- The shared UI fetches nothing from a network here: every asset it needs is
  served from `ui/`, and previews are rendered in Python. (The static edition
  fetches renderers from a CDN; this one has no reason to.) The `/f/` UI's htmx
  and mermaid CDN tags are why *its* browser tests cannot run offline.
- Client-side keyboard navigation must keep the browser URL in sync with the visible Finder state; if a key handler changes columns/preview without an HTMX request, it must update history explicitly.
- PWA static assets (`/manifest.json`, `/sw.js`, `/icons/*`) are served from
  `src/filemill/static/` and are bundled with the package; they are
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
timeout 1800 uv run pytest     # everything, browser tests included

# Just the 56 real-browser tests. Needs PLAYWRIGHT_BROWSERS_PATH. The 29 in
# test_browser_keyboard.py alone took 342 s on a 4-core host, so budget minutes.
timeout 1800 uv run pytest tests/test_browser_keyboard.py tests/test_browser_new_ui.py
```

> **Important:** always wrap `uv run pytest` in a shell-level timeout when
> calling it from a script or agent tool. SSE streaming tests that misbehave can
> otherwise block indefinitely (see
> [issue #17](ISSUES.md#17--fix-hanging-sse-test-test_sse_reload_exists_with_live_mode)).
> Use 1800 seconds, not 120: the browser tests alone take about 9 minutes.

### Do Not Pass `--with playwright==…`

Earlier versions of this file told you to. The command it gave now fails:

```
$ uv run --with "playwright==1.57.0" pytest tests/test_browser_new_ui.py
BrowserType.launch: Executable doesn't exist at
  .../chromium_headless_shell-1200/chrome-headless-shell-linux64/chrome-headless-shell
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║     playwright install                                     ║
╚════════════════════════════════════════════════════════════╝
```

Ignore that banner. Each Playwright release carries exactly one browser
revision, each Nix browser bundle carries exactly one, and they have to be the
same one. `$PLAYWRIGHT_BROWSERS_PATH` here holds `chromium-1228` and
`chromium_headless_shell-1228`, so 1.61.x is the only version that launches:
1.57.0 asks for revision 1200 and 1.62.0 asks for 1234. `pyproject.toml` pins
`playwright~=1.61.0` for that reason, and `--with` overrides the pin. Running
`playwright install` would download a fourth copy of a browser Nix already
provides, so do not run it. Re-pin from the constraint file instead:

```bash
uv lock --upgrade-package "$(grep -E '^playwright[=<>~!]' "$UV_CONSTRAINT")"
```

### The `/f/` Browser Tests Need Outbound Network

`tests/test_browser_keyboard.py` drives the HTMX finder shell, which loads htmx
from `unpkg.com` and mermaid from `cdn.jsdelivr.net`. With no route to those two
hosts the page draws `#col-0` and then ignores every click, so the tests fail on
their navigation assertions and look like a routing regression. Behind an
authenticated proxy the tell is `407 Proxy Authentication Required` in the
*browser* console, which pytest never prints. `_proxy_from_env()` in that file
reads `$HTTPS_PROXY` and passes the credentials to Chromium, which reads the
variable but drops the credentials in it.

`tests/test_browser_new_ui.py` drives the `/n/` shared UI, which serves every
asset itself, so those 27 tests pass with no network at all. Measured on a host
with no proxy credentials given to Chromium: 27 passed in 115 s.

Two measurements of this file disagree, and the disagreement is unresolved. On
2026-08-18 one agent recorded 27 passed in 115 s and 118 s on a 4-core host,
including the two local-folder tests three times alone at 9.42 s, 9.26 s and
8.60 s, and passing under four busy loops in 24.68 s. A second agent on a
different host recorded `test_local_files_are_still_rendered_by_python` and
`test_local_source_is_still_highlighted_by_pygments` failing on
`wait_for_selector("#preview .pv-rich h1")`, with and without proxy variables
set, and running only those two. Nobody has explained the difference. If you see
those two fail, you are the third data point: capture the browser console and
whether `POST /api/render` answered, and say which host you were on.

`test_nothing_is_fetched_from_a_cdn` is what holds the `/n/` UI to that, and it
now watches both halves. The served half goes through `preview-http.js` and
`GET /api/preview`; the local-folder half goes through `preview-upload.js` and
`POST /api/render`. It used to watch only the served half, which left the half
its own docstring is about unchecked.

The adapter that would break this is `ui/adapters/preview-rich.js`, which
lazy-loads a renderer from a CDN. `tools/sync-ui.py` does not vendor it into
`src/pykofinder/ui/adapters/`, and that omission is load-bearing. If a future
sync ships it, `test_nothing_is_fetched_from_a_cdn` fails with the fetched URL in
the assertion, which is the failure you want.

### Wait for an Element, Never for a Duration

The `/f/` shell fills its columns after the page reports `networkidle`, so
`page.wait_for_timeout(900)` is a guess about how loaded the machine is. On this
4-core host with four busy loops running, 2 of 6 attempts still had no `#col-0`
at 800 ms. `_click_item()` waits for the entry with `page.wait_for_function` and
then clicks it, so a missing entry raises a `TimeoutError` naming the column.
Write new browser assertions the same way. A helper that returns quietly when it
finds nothing turns a slow machine into an assertion failure three lines away
from the cause.

## Submitting changes

1. Open an issue in `ISSUES.md` and set its status to `in-progress`.
2. Add a matching `[~]` entry in `TASKS.md`.
3. Follow the TDD cycle above.
4. Update `README.md`, `CONTRIBUTING.md`, `ISSUES.md`, and `TASKS.md`.
5. Mark the issue closed before committing.
