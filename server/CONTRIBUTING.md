# Contributing to Filemill — server edition

## Project context

Filemill is a column-view file browser and previewer in the style of macOS
Finder. The server edition serves it as a Starlette web application. Click a
column entry to open a directory. Files preview inline: Markdown, DOCX, PPTX,
PDF, images, plain text, and code with syntax highlighting. PPTX shows extracted
slide text. See the [root edition/renderer table](../README.md) for current
capabilities, network behavior and implementation links.

### Source layout

```
src/filemill/
├── app.py          # Starlette app and routes
├── api.py          # /api/* request handlers behind the shared UI
├── cli.py          # Typer CLI entry point
├── env.py          # FILEMILL_* variables, PYKOFINDER_* fallback
├── mutations.py    # Origin, Host and token checks for save and delete
├── paths.py        # resolve_safe() and symlink bookmark zones
├── preview.py      # Server RST, media and source preview dispatcher
├── pwa.py          # /manifest.json, /sw.js and /icons/ handlers
├── urls.py         # View state and canonical URLs
├── vfs.py          # Virtual-filesystem registry + provider protocol
├── providers/      # VFS backends (SQLite, VTT, archives, Git bundles)
├── static/         # Bundled PWA assets (manifest.json, sw.js, icons/)
└── ui/             # The shared frontend; the repo root's ui/ symlinks here

tests/
├── test_api.py               # /api/* contract + the shared UI's shell
├── test_app.py               # Route-level integration tests
├── test_archive_provider.py  # tar and zip VFS provider unit tests
├── test_browser_keyboard.py  # Keyboard navigation, driven in a real browser
├── test_browser_new_ui.py    # The shared UI, driven in a real browser
├── test_browser_waits.py     # Rejects Playwright duration-wait calls
├── test_cli.py               # CLI smoke tests
├── test_docs.py              # Documents agree with the pins and the code
├── test_file_kind.py         # Server file classification
├── test_gitbundle_provider.py # Git bundle VFS provider unit tests
├── test_mutation_policy.py   # Save and delete authorization
├── test_preview.py           # Preview rendering (all file types)
├── test_providers_sqlite.py  # SQLite VFS provider unit tests
├── test_pytest_config.py     # Server runs elect ../pytest.ini and ../conftest.py
├── test_pwa.py               # PWA assets (manifest, SW, icons, head tags)
├── test_resolve_safe.py      # Path-safety logic (paths.resolve_safe)
├── test_resource_routes.py   # The one directory rule in resource()
├── test_resource_safety.py   # Path containment in resource()
├── test_routes_new.py        # Additional route coverage
├── test_suppression_links.py # Python noqa comments link to an issue
├── test_urls.py              # View state and canonical URLs
├── test_vfs.py               # VFS registry and provider protocol
└── test_vtt_provider.py      # VTT VFS provider unit tests
```

### The shared UI

The [root README](../README.md) is the current edition/renderer reference.
The frontend lives in `src/filemill/ui/`, with the repository's `../ui/`
symlink pointing to it. The static builder concatenates that same module graph;
the server serves it through [`app.py`](src/filemill/app.py).

Virtual filesystems use the same adapter. A `.db` file lists as a directory
when its provider yields entries. Its children carry a **`vpath`**: a path
inside the file. An entry with a `vpath` keeps its parent's real path and
descends virtually. An entry without one joins its name to the path. The server
puts the `vpath` on the entries it returns, so `ui/core/` never learns that
virtual nodes exist.

`/sample.db/users/1` is one URL that names two things. `api.split_vfs()`
separates them and validates a deep link. The joined form exists only in the
address bar.

[`app-http.js`](../ui/adapters/app-http.js) selects browser rendering for
Markdown, DOCX and PPTX. Local-folder bytes stay in the browser rather than
being uploaded to a render endpoint. RST local-folder routing remains an A8
limit, documented in the root README.

[`pyproject.toml`](pyproject.toml) excludes static/native entry points and
adapters from the wheel. The server's module graph, including `preview-rich.js`
and its vendored dependencies, ships inside the package. There is no packaging
copy of the shared UI to refresh.

The resource route serves the shared UI. `index()` hands `/` to `resource()`. A directory, `/` included,
without an index returns `_ui_shell(state)`. The URL path is the file path relative to
ROOT, with no prefix. A bare file path returns its own bytes, because `raw` is
the default view and that branch returns before the shell one.
`filemill=render` or `highlight` puts the shell around a file.
`layout=full-columns` (default) or `compressed-columns` only changes the
`data-layout` attribute the client reads.

### Key invariants

- [`paths.py`](src/filemill/paths.py) checks paths against the root and allowed
  direct-child symlink bookmark zones. [`app.py`](src/filemill/app.py) also
  validates the final directory index. Mutation routes check Origin, Host and
  a per-process token before path resolution or body consumption. See
  [SECURITY.md](../SECURITY.md). A4 and A5 remain open.
- `/w/` and `/n/` are ordinary resource paths, with no alias or redirect.
  See [ADR 0088](../docs/adr/0088-remove-named-mount-and-alternate-shell-routes.md).
- There is no JavaScript build step.
- Every filesystem path in the `/api/*` and resource routes is **relative to ROOT**.
  `api.rel_to_abs` refuses an absolute path, because `ROOT / "/etc/passwd"` is
  `/etc/passwd`. `resolve_safe()` then checks containment.
- Browser renderer dependencies for Markdown and DOCX are served locally.
  Document references can still request external resources; see the root README.
- A keyboard handler that changes columns or the preview must update the
  browser URL. The URL and the visible Finder state must agree.
- `src/filemill/static/` holds the PWA assets `/manifest.json`, `/sw.js` and
  `/icons/*`. `_reorder_routes()` puts them, `/ui/` and `/api/*` before
  the resource catch-all route, `/{path:path}`. Without that, the catch-all
  swallows every `.js` and `.css` the shared UI asks for, and the page is blank.
- The UI shell registers the [service worker](src/filemill/static/sw.js).
  It asks the network first for every GET it handles, except an exact
  content-hashed `/ui/` module URL, and keeps complete answers as offline
  copies: shell pages marked `X-Filemill-Shell`, UI assets, listings, file
  bytes and previews. Only when the server does not answer does
  it reply with a copy marked `X-Filemill-Offline`, or a valid 503 without one.
  Non-GET, `/api/search`, Range and `cache: "no-store"` requests bypass it.
  [`server-status.js`](../ui/adapters/server-status.js) turns those answers
  into the offline indicator. See
  [ADR 0089](../docs/adr/0089-an-offline-server-shows-older-copies-with-an-indicator.md).

---

## Development rules

- **TDD (red-green)** – write a failing test first, then make it pass. Do not
  write production code without a failing test.
- **Coverage** – every new or changed behaviour has a test.
  [CI](../.github/workflows/publish.yml) measures branch coverage with
  `--cov=src/filemill --cov-branch --cov-report=term-missing`; it sets no
  coverage percentage threshold. Unit and integration tests use pytest.
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

# Only the real-browser tests. Install matching browsers first. The two files
# together took 246 s on a 4-core host, so budget minutes.
timeout 1800 uv run pytest tests/test_browser_keyboard.py tests/test_browser_new_ui.py
```

pytest takes its configuration and shared fixtures from `../pytest.ini` and
`../conftest.py`. Keep `[tool.pytest.ini_options]` out of `pyproject.toml`: it
would become the rootdir and hide those fixtures. `tests/test_pytest_config.py`
checks this.

> **Important:** wrap `uv run pytest` in a shell-level timeout when a script or
> an agent tool calls it. A hung browser test can block without end. Use 1800
> seconds, not 120: the browser tests alone take about 9 minutes.

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

Each Playwright release requires a matching browser revision.
`--with "playwright==X"` overrides the pin, so run the suites with `uv run pytest`
from `server/` instead.
Install the locked release's Chromium with `uv run playwright install chromium`.
If your environment provides a managed browser bundle, set
`PLAYWRIGHT_BROWSERS_PATH` to its directory. Verify that its revision matches
Playwright before running tests. For a bundle such as Nix, select the matching
Playwright release and update the lock when the bundle changes. Do not download
another browser to work around a mismatch with a managed bundle.

### No proxy for the browser tests

The browser tests hand no proxy to Chromium (`_ui_page` in
`tests/test_browser_keyboard.py`). The shared UI serves every asset itself, so
the tests need no network, and `test_nothing_is_fetched_from_a_cdn` in
`tests/test_browser_new_ui.py` keeps it that way. Measured on a host with no
proxy credentials given to Chromium: 34 passed in 95 s.

### Historical local-folder measurements

Superseded 2026-10-19. The upload renderer and the two named Python-rendering
tests were removed when rendering moved to the browser. The following records
the 2026-08-18 investigation, not current test instructions. On
2026-08-18 one agent recorded 27 passed in 115 s and 118 s on a 4-core host.
`test_local_files_are_still_rendered_by_python` and
`test_local_source_is_still_highlighted_by_pygments` passed three times alone
at 9.42 s, 9.26 s and 8.60 s, and passed under four busy loops in 24.68 s. A
second agent on a different host recorded the same two failing, with and
without proxy variables set, and when running only those two.

The second agent's runs showed that `POST /api/render` completes, and that
`#preview .pv-rich h1` never appears. Slowness and the round trip are not the
cause.

The former `ui/adapters/preview-upload.js` had two silent branches:

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

Current served and local-folder preview tests are in
[`test_browser_new_ui.py`](tests/test_browser_new_ui.py), including
`test_nothing_is_fetched_from_a_cdn`. Renderer selection is implemented in
[`app-http.js`](../ui/adapters/app-http.js).

### Wait for an Element, Never for a Duration

Use Playwright `expect` assertions or `page.wait_for_function` predicates for
navigation, preview content and asynchronous work. Wait for the expected value,
not merely for an old element to exist. Scroll checks must include the dial's
range rebase; race checks must observe the delayed operation starting and
finishing. Do not use a sleep to guess when the UI is ready.

A deliberate response delay is test input, not synchronization. For example,
`test_declined_json_member_recovers_after_refresh` in [the served UI tests]
delays a response by 0.2 seconds to supply slow input. Its loading/error state
predicate and DOM conditions determine completion: the chevron and pending
column disappear, the preview shows the error, and refresh restores the member.
The delay does not establish that the pending column opened before rejection.
A delay alone does not prove overlap; a race test must observe the delayed
operation starting and finishing.

For history races, hold the response until the loading column is observable,
then release it and check both the final URL and history length. A preview
alone cannot prove that an earlier temporary column added no history entry.
The [outline history regression] covers both a declined file and a confirmed
outline without a fixed delay.

The [browser-wait guard] scans static Python scripts and server tests for
`wait_for_timeout`. It does not ban every sleep or prove that all other waits
are correct. Slow input is allowed; arbitrary readiness sleeps are not.

## Submitting changes

1. Move the issue in the root `TASKS.md` as its Rules section says.
2. Follow the TDD cycle above.
3. Update `README.md`, `CONTRIBUTING.md` and the root `TASKS.md`.
4. Mark the issue completed before you commit.

[the served UI tests]: tests/test_browser_new_ui.py
[browser-wait guard]: tests/test_browser_waits.py
[outline history regression]: tests/test_browser_new_ui.py
