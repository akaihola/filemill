# Contributing to Filemill — server edition

## Project context

Filemill is a column-view file browser and previewer in the style of macOS
Finder. The server edition serves it as a FastHTML web application. Click a
column entry to open a directory. Files preview inline: Markdown, DOCX, PPTX,
PDF, images, plain text, and code with syntax highlighting.

### Source layout

```
src/filemill/
├── app.py          # FastHTML app and routes
├── api.py          # JSON/fragment API behind the shared UI (/api/*)
├── cli.py          # Typer CLI entry point
├── env.py          # FILEMILL_* variables, PYKOFINDER_* fallback
├── paths.py        # resolve_safe() and the named-mount map
├── preview.py      # Preview dispatcher (md / docx / pptx / pdf / img / code / raw)
├── pwa.py          # /manifest.json, /sw.js and /icons/ handlers
├── rendering.py    # markdown-it-py instance with plugins
├── urls.py         # View state and canonical URLs
├── vfs.py          # Virtual-filesystem registry + provider protocol
├── providers/      # VFS backends (SQLite, JSON, VTT)
├── static/         # Bundled PWA assets (manifest.json, sw.js, icons/)
└── ui/             # The shared frontend; the repo root's ui/ symlinks here

tests/
├── conftest.py               # Shared fixtures (tmp dirs, test client)
├── test_api.py               # /api/* contract + the shared UI's shell
├── test_app.py               # Route-level integration tests
├── test_browser_keyboard.py  # Keyboard navigation, driven in a real browser
├── test_browser_new_ui.py    # The shared UI, driven in a real browser
├── test_cli.py               # CLI smoke tests
├── test_preview.py           # Preview rendering (all file types)
├── test_providers_sqlite.py  # SQLite VFS provider unit tests
├── test_pwa.py               # PWA assets (manifest, SW, icons, head tags)
├── test_rendering.py         # Markdown pipeline
├── test_resolve_safe.py      # Path-safety logic (paths.resolve_safe)
├── test_resource_routes.py   # The one directory rule in resource()
├── test_resource_safety.py   # Path containment in resource()
├── test_routes_new.py        # Additional route coverage
├── test_urls.py              # View state and canonical URLs
├── test_vfs.py               # VFS registry and provider protocol
└── test_vtt_provider.py      # VTT VFS provider unit tests
```

### The shared UI

The frontend is `src/filemill/ui/`. The repository root's `../ui/` is a
symlink to it. Both paths reach one directory. The static edition builds its
single-file bundle from it, and this package serves it. The two editions are
one application. The only difference is the adapters that the shared `core/`
receives:

| | **static** | **server** (here) |
| --- | --- | --- |
| filesystem | File System Access API | `GET /api/dir` |
| preview | text/image, in the browser | `GET /api/preview` — **this module's renderers**; a database row travels as JSON on its `/api/dir` entry and the client draws it |
| router | `#r=root&p=a/b.md` | `/n/a/b.md` |

Virtual filesystems use the same adapter. A `.db` file lists as a directory
when its provider yields entries. Its children carry a **`vpath`**: a path
inside the file. An entry with a `vpath` keeps its parent's real path and
descends virtually. An entry without one joins its name to the path. The server
puts the `vpath` on the entries it returns, so `ui/core/` never learns that
virtual nodes exist.

`/n/sample.db/users/1` is one URL that names two things. `api.split_vfs()`
separates them and validates a deep link. The joined form exists only in the
address bar.

This is why `preview.py`, `rendering.py`, `vfs.py` and `providers/` have no
JavaScript port, and why `POST /api/render` exists. When the browser opens a
*local* folder, the server cannot read it. The page posts the bytes, and the
same markdown-it-py, Pygments and mammoth pipeline renders them.

**`src/filemill/ui/` is the shared frontend itself, not a copy.** A wheel
cannot reach outside its package at runtime, so the frontend is inside the
package and the repository root's `../ui/` is a symlink. Edit it through either
path. There is no copy to refresh.

`wheel-exclude` in `pyproject.toml` keeps three static-only adapters out of
the wheel: `app-fsa.js`, `preview-rich.js` and `router-hash.js`. The server
shell loads the adapters listed in `_UI_ADAPTERS` in `app.py`.

One repository and one set of files means that a UI change lands in both
editions in one commit. `ui/adapters/README.md` documents the three ports.

The shared UI is mounted at `UI_BASE = "/n/"`, and the resource route serves
it too. `index()` hands `/` to `resource()`. A directory under a column layout,
`/` included, returns `_ui_shell(state, "/")`. The URL path is the file path
relative to ROOT, with no prefix. A bare file path returns its own bytes,
because `raw` is the default view and that branch returns before the column
one. `filemill=render` or `highlight` puts the shell around a file.
`layout=no-columns` renders through `_page_html()`.

### Key invariants

- All routes stay under a configurable `ROOT` directory. `resolve_safe()` in
  `paths.py` refuses every path that escapes the root, symlinks included.
- Static `/w/` URLs use named mounts. The root directory is `/w/<ROOT.name>/...`.
  Each direct symlink child of ROOT is `/w/<symlink-name>/...`.
- There is no JavaScript build step.
- Every path in the `/api/*` and `/n/` routes is **relative to ROOT**.
  `api.rel_to_abs` refuses an absolute path, because `ROOT / "/etc/passwd"` is
  `/etc/passwd`. `resolve_safe()` then checks containment.
- The shared UI fetches nothing from the network in this edition. `ui/` serves
  every asset, and Python renders the previews.
- A keyboard handler that changes columns or the preview must update the
  browser URL. The URL and the visible Finder state must agree.
- `src/filemill/static/` holds the PWA assets `/manifest.json`, `/sw.js` and
  `/icons/*`. `_reorder_routes()` puts them, `/ui/`, `/n/` and `/api/*` before
  FastHTML's static catch-all route. Without that, the catch-all swallows
  every `.js` and `.css` the shared UI asks for, and the page is blank.
- The UI shell registers the service worker. The worker bypasses non-GET
  requests and `/api/*`, so it cannot cache file data or intercept local-file
  uploads.

---

## Development rules

- **TDD (red-green)** – write a failing test first, then make it pass. Do not
  write production code without a failing test.
- **Full test coverage** – every new or changed behaviour has a test. The
  suite runs at 100% branch coverage. Unit and integration tests use pytest.
- **Documentation stays current** – update `README.md` and the root `TASKS.md`
  in the same change.
- **Simplify** – look for a simpler form on every pass. Less code is better
  code.
- **Frequent conventional commits** – commit at every logical checkpoint with
  a conventional-commit prefix: `feat:`, `fix:`, `test:`, `docs:`,
  `refactor:`, `chore:`, `style:`, `perf:`.

## Running tests

```bash
uv sync
timeout 1800 uv run pytest     # everything, browser tests included

# Only the real-browser tests. Needs PLAYWRIGHT_BROWSERS_PATH. The two files
# together took 246 s on a 4-core host, so budget minutes.
timeout 1800 uv run pytest tests/test_browser_keyboard.py tests/test_browser_new_ui.py
```

> **Important:** wrap `uv run pytest` in a shell-level timeout when a script or
> an agent tool calls it. A misbehaving SSE streaming test can block without
> end (see issue #17, fix hanging SSE test). Use 1800 seconds, not 120: the
> browser tests alone take about 9 minutes.

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

Ignore that banner. Each Playwright release carries one browser revision.
Each Nix browser bundle carries one. They must be the same one.
`$PLAYWRIGHT_BROWSERS_PATH` holds `chromium-1228` and
`chromium_headless_shell-1228`, so only 1.61.x launches. 1.57.0 asks for
revision 1200 and 1.62.0 asks for 1234. `pyproject.toml` pins
`playwright~=1.61.0` for that reason, and `--with` overrides the pin.
`playwright install` downloads a fourth copy of a browser that Nix provides.
Do not run it. Re-pin from the constraint file instead:

```bash
uv lock --upgrade-package "$(grep -E '^playwright[=<>~!]' "$UV_CONSTRAINT")"
```

### Proxy credentials for the browser tests

`_proxy_from_env()` in `tests/test_browser_keyboard.py` reads `$HTTPS_PROXY`
and passes its credentials to Chromium. Chromium reads the variable but drops
the username and password in it. Behind an authenticated proxy the symptom is
`407 Proxy Authentication Required` in the *browser* console, which pytest
never prints.

`tests/test_browser_new_ui.py` drives the shared UI, which serves every asset
itself, so those tests pass with no network. Measured on a host with no proxy
credentials given to Chromium: 34 passed in 95 s.

### Two Measurements of the Local-Folder Tests Disagree

The disagreement is unresolved, and both conditions are reproducible. On
2026-08-18 one agent recorded 27 passed in 115 s and 118 s on a 4-core host.
`test_local_files_are_still_rendered_by_python` and
`test_local_source_is_still_highlighted_by_pygments` passed three times alone
at 9.42 s, 9.26 s and 8.60 s, and passed under four busy loops in 24.68 s. A
second agent on a different host recorded the same two failing, with and
without proxy variables set, and when running only those two.

The second agent's runs showed that `POST /api/render` completes, and that
`#preview .pv-rich h1` never appears. Slowness and the round trip are not the
cause.

Look at `ui/adapters/preview-upload.js`. It has two branches that are silent
by design:

```js
if (!r.ok) return PreviewLocal.render(node);   /* draws no .pv-rich */
return html.trim() ? `<div class="pv-rich">${html}</div>` : null;
```

A non-2xx response falls back to a renderer that emits no `.pv-rich`. An empty
body draws nothing. Both look like a slow machine from the test's side.
`_click_local()` reports which one happened. Its two failure messages, verified
by mutating `api.render_upload()`:

```
POST /api/render answered 500 for local.md, so preview-upload.js fell back
silently and drew no .pv-rich. First 300 bytes: 'boom'

#preview .pv-rich h1 never appeared for local.md. POST /api/render answered 200
with 48 bytes, and #preview .pv-rich count is 1. A count of 0 means nothing was
injected; a count of 1 means the server rendered something without that element
in it. First 300 bytes: '<div class="preview-error">no heading here</div>'
```

If you hit this, run those two tests and paste the message. It names the
status and the first 300 bytes the server sent. That is the cause, not a
timeout.

`test_nothing_is_fetched_from_a_cdn` holds the shared UI to that. It watches
both halves. The served half goes through `preview-http.js` and
`GET /api/preview`. The local-folder half goes through `preview-upload.js`
and `POST /api/render`.

### Wait for an Element, Never for a Duration

`page.wait_for_timeout(900)` is a guess about the load on the machine. On a
4-core host with four busy loops, 2 of 6 attempts had no `#col-0` at 800 ms.
`_click_item()` waits for the entry with `page.wait_for_function` and then
clicks it, so a missing entry raises a `TimeoutError` that names the column.
Write new browser assertions the same way. A helper that returns quietly when
it finds nothing turns a slow machine into an assertion failure three lines
away from the cause.

## Submitting changes

1. Move the issue in the root `TASKS.md` as its Rules section says.
2. Follow the TDD cycle above.
3. Update `README.md`, `CONTRIBUTING.md` and the root `TASKS.md`.
4. Mark the issue completed before you commit.
