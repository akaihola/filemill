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
├── styles.py       # Legacy /f/ CSS and scripts
├── vfs.py          # Virtual-filesystem registry + provider protocol
├── providers/      # VFS backends (SQLite, JSON, CSV)
├── static/         # Bundled PWA assets (manifest.json, sw.js, icons/)
└── ui/             # The shared frontend; the repo root's ui/ symlinks here

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

The frontend lives at **`src/filemill/ui/`**, which the repository root's
`../ui/` symlinks to — one directory, reachable by either path. The
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

**`src/filemill/ui/` is the shared frontend itself, not a copy.** It lives
inside the package because a wheel cannot reach outside itself at runtime, and
the repository root's `../ui/` is a symlink to it. Edit it through either path;
there is no copy to refresh and nothing that can go stale.

Three adapters there belong to the static edition alone — `app-fsa.js`,
`preview-rich.js` and `router-hash.js`. The server shell never loads them, and
`wheel-exclude` in `pyproject.toml` keeps them out of the wheel.

Because it is one repository and one set of files, a UI change lands in both
projects in one commit. `ui/adapters/README.md` documents the three ports.

The shared UI is mounted at `UI_BASE = "/n/"`, and the resource route serves
it too. `index()` hands `/` to `resource()`, and a directory under a column
layout — `/` itself included — comes back as `_ui_shell(state, "/")`, where
the URL path *is* the file path relative to ROOT, with no prefix. A bare
file path is still its own bytes, because `raw` is the default view and
that branch returns before the column one; it takes `filemill=render` or
`highlight` to get the shell around a file. `layout=no-columns` renders
through `_page_html()`. The shared UI is mounted at `/n/`; the legacy HTMX UI
remains at `/f/` for compatibility.

### Key invariants

- All routes are under a configurable `ROOT` directory; `_resolve_safe()` in
  `app.py` enforces that no path escapes that root (symlinks included).
- Static `/w/` URLs use named mounts: the root directory is exposed as
  `/w/<ROOT.name>/...`, and each direct symlink child of ROOT is exposed as
  `/w/<symlink-name>/...`.
- Column pruning is done client-side via a small `<script>` injected into each
  click response – no server round-trip needed.
- The shared UI at `/n/` drives navigation in the server edition; the legacy
  HTMX UI remains available at `/f/` for compatibility. There is no JavaScript
  build step in either UI.
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
- Both UI shells register the service worker. The worker bypasses non-GET
  requests and `/api/*`, so it cannot cache file data or intercept local-file
  uploads.

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

# Just the 67 real-browser tests. Needs PLAYWRIGHT_BROWSERS_PATH. The two files
# together took 246 s on a 4-core host, so budget minutes.
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

### The Legacy `/f/` Browser Tests Need Outbound Network

Most of `tests/test_browser_keyboard.py` now drives the shared UI at `/`, which
fetches nothing; this section is about the tests still driving the compatibility
shell at `/f/`. That shell loads htmx from `unpkg.com` and mermaid from
`cdn.jsdelivr.net`. With no route to those two hosts the page draws `#col-0`
and then ignores every click, so a test that clicks fails on its navigation
assertions and looks like a routing regression.

Three of the `/f/` tests actually need those hosts and seven do not. Measured
by pointing `$HTTPS_PROXY` at a dead port with `$NO_PROXY` bypassing
localhost, so only the CDN requests fail: 3 failed, 7 passed.

- `test_legacy_query_url_canonicalizes_after_nested_navigation` clicks through
  htmx, being the only caller of `_click_item()`.
- `test_mobile_file_restore_scroll_position_is_not_zero` and
  `test_mobile_restore_behavior_preview_assertions` are the only `/f/` tests
  calling `_wait_for_finder_scroll()`, which waits for `#finder.scrollLeft` to
  pass 0. The deep-link restore in `styles.py` calls `htmx.process()` before
  `scrollFinderToReveal()` inside a promise chain that ends in an empty
  `.catch`, so an undefined `htmx` throws, the error is swallowed, the finder
  never scrolls, and the wait times out after 20 s.

The other seven only read what the server already rendered, so htmx never has
to run for them.

Behind an authenticated proxy the tell is `407 Proxy Authentication
Required` in the *browser* console, which pytest never prints.
`_proxy_from_env()` in that file reads `$HTTPS_PROXY` and passes the
credentials to Chromium, which reads the variable but drops the credentials
in it.

`tests/test_browser_new_ui.py` drives the `/n/` shared UI, which serves every
asset itself, so those 34 tests pass with no network at all. Measured on a host
with no proxy credentials given to Chromium: 34 passed in 95 s.

### Two Measurements of the Local-Folder Tests Disagree

The disagreement is unresolved, and both conditions are reproducible. On
2026-08-18 one agent recorded 27 passed in 115 s and 118 s on a 4-core host,
including `test_local_files_are_still_rendered_by_python` and
`test_local_source_is_still_highlighted_by_pygments` three times alone at 9.42 s,
9.26 s and 8.60 s, and passing under four busy loops in 24.68 s. A second agent
on a different host recorded those same two failing, with and without proxy
variables set, and when running only those two.

What the second agent's runs established: `POST /api/render` completes, and
`#preview .pv-rich h1` still never appears. That rules out slowness and rules out
the round trip.

The mechanism to look at is in `ui/adapters/preview-upload.js`, which has two
branches that are silent by design:

```js
if (!r.ok) return PreviewLocal.render(node);   /* draws no .pv-rich */
return html.trim() ? `<div class="pv-rich">${html}</div>` : null;
```

A non-2xx falls back to a renderer that emits no `.pv-rich`, and an empty body
draws nothing. Both look like a slow machine from the test's side. `_click_local()`
now reports which one happened. Its two failure messages, verified by mutating
`api.render_upload()`:

```
POST /api/render answered 500 for local.md, so preview-upload.js fell back
silently and drew no .pv-rich. First 300 bytes: 'boom'

#preview .pv-rich h1 never appeared for local.md. POST /api/render answered 200
with 48 bytes, and #preview .pv-rich count is 1. A count of 0 means nothing was
injected; a count of 1 means the server rendered something without that element
in it. First 300 bytes: '<div class="preview-error">no heading here</div>'
```

If you hit this, run those two tests and paste the message. It names the status
and the first 300 bytes the server sent, which is the cause rather than a
timeout.

`test_nothing_is_fetched_from_a_cdn` is what holds the `/n/` UI to that, and it
now watches both halves. The served half goes through `preview-http.js` and
`GET /api/preview`; the local-folder half goes through `preview-upload.js` and
`POST /api/render`. It used to watch only the served half, which left the half
its own docstring is about unchecked.

The adapter that would break this is `ui/adapters/preview-rich.js`, which
lazy-loads a renderer from a CDN. The server shell never loads it —
`_UI_ADAPTERS` omits it — and `wheel-exclude` in `pyproject.toml` keeps it out
of the wheel, so an installed package cannot serve it at all. Both are
load-bearing: add it to `_UI_ADAPTERS` and `test_nothing_is_fetched_from_a_cdn`
fails with the fetched URL in the assertion, which is the failure you want.

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
