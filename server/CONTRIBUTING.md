# Contributing to Filemill — server edition

## Project context

The [root edition/renderer table] describes
capabilities. The [shared contributor guide] owns setup,
model boundaries, quality gates, commit style and writing rules. This guide
covers server modules and browser prerequisites.

### Source layout

Selected modules and tests; this is not a complete file inventory.

```
src/filemill/
├── app.py          # Starlette app and routes
├── api.py          # /api/* request handlers behind the shared UI
├── cli.py          # Typer CLI entry point
├── env.py          # FILEMILL_* variables, PYKOFINDER_* fallback
├── mutations.py    # All-route Host checks; Origin and token mutation checks
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

The [root README] is the current edition/renderer reference.
The frontend lives in [server/src/filemill/ui/], with the repository's [server/src/filemill/ui/]
symlink pointing to it. The static builder concatenates that same module graph;
the server serves it through [server/src/filemill/app.py].

Virtual filesystems use the same adapter. A `.db` file lists as a directory
when its provider yields entries. Its children carry a **`vpath`**: a path
inside the file. An entry with a `vpath` keeps its parent's real path and
descends virtually. An entry without one joins its name to the path. The server
puts `vpath` on returned entries. Core still checks it to suppress deletion
of members. HTTP content-search URLs belong to the filesystem adapter. The architecture review's A6/A12
findings track these remaining identity and dependency boundaries.

`/sample.db/users/1` is one URL that names two things. `api.split_vfs()`
separates them and validates a deep link. The joined form exists only in the
address bar.

[server/src/filemill/ui/adapters/app-http.js] selects browser rendering for
Markdown, DOCX and PPTX. Local-folder bytes stay in the browser rather than
being uploaded to a render endpoint. RST local-folder routing remains an A8
limit, documented in the root README.

[server/pyproject.toml] excludes static/native entry points and
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

- [server/src/filemill/paths.py] checks paths against the root and allowed
  direct-child symlink bookmark zones. [server/src/filemill/app.py] also
  validates the final directory index. Mutation routes check Origin, Host and
  a per-process token before path resolution or body consumption. See
  [SECURITY.md]. Revision-checked atomic saves resolve A4;
  [the replacement decision]
  records their limits. A5 now concerns the static worker.
- `/w/` and `/n/` are ordinary resource paths, with no alias or redirect.
  See [ADR 0088].
- Shared modules run without a development build. Rebuild the committed static
  bundle when those modules change.
- Every filesystem path in the `/api/*` and resource routes is **relative to ROOT**.
  `api.rel_to_abs` refuses an absolute path, because `ROOT / "/etc/passwd"` is
  `/etc/passwd`. `resolve_safe()` then checks containment.
- Browser renderer dependencies for Markdown and DOCX are served locally.
  Document references can still request external resources; see the root README.
- A keyboard handler that changes columns or the preview must update the
  browser URL. The URL and the visible Finder state must agree.
- [server/src/filemill/static/] holds the PWA assets `/manifest.json`, `/sw.js` and
  `/icons/*`. `_reorder_routes()` puts them, `/ui/` and `/api/*` before
  the resource catch-all route, `/{path:path}`. Without that, the catch-all
  swallows every `.js` and `.css` the shared UI asks for, and the page is blank.
- The UI shell registers the [service worker].
  It asks the network first for every GET it handles, except an exact
  content-hashed `/ui/` module URL, and keeps complete answers as offline
  copies: shell pages marked `X-Filemill-Shell`, UI assets, listings, file
  bytes and previews. Only when the server does not answer does
  it reply with a copy marked `X-Filemill-Offline`, or a valid 503 without one.
  Non-GET, `/api/search`, Range and `cache: "no-store"` requests bypass it.
  [server/src/filemill/ui/adapters/server-status.js] turns those answers
  into the offline indicator. See
  [ADR 0089].

---

## Running tests

Run the following from [server/]. For static, model and gate commands use the
[shared contributor guide].

```bash
uv sync
timeout 1800 uv run pytest     # server tests, browser tests included

# Only the real-browser tests. Install matching browsers first. The two files
# need Chromium and Firefox. Budget minutes; old timing results are historical.
timeout 1800 uv run pytest tests/test_browser_keyboard.py tests/test_browser_new_ui.py
```

pytest takes its configuration and shared fixtures from [pytest.ini] and
[conftest.py]. Keep `[tool.pytest.ini_options]` out of [server/pyproject.toml]: it
would become the rootdir and hide those fixtures. [server/tests/test_pytest_config.py]
checks this.

> **Important:** wrap `uv run pytest` in a shell-level timeout when a script or
> an agent tool calls it. A hung browser test can block without end. Use 1800
> seconds for full suites; historical browser runs took several minutes.

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
from [server/] instead.
Install the locked release's browsers with
`uv run playwright install --with-deps chromium firefox`. Chromium runs the
main suites; the heading-fragment check also parametrizes Firefox. The
`--with-deps` option can require administrator access for system packages.
If your environment provides a managed browser bundle, set
`PLAYWRIGHT_BROWSERS_PATH` to its directory. Verify that its revision matches
Playwright before running tests. For a bundle such as Nix, select the matching
Playwright release and update the lock when the bundle changes. Do not download
another browser to work around a mismatch with a managed bundle.

### No proxy for the browser tests

The browser tests hand no proxy to Chromium (`_ui_page` in
[server/tests/test_browser_keyboard.py]). The shared UI serves every asset itself, so
the tests need no network, and `test_nothing_is_fetched_from_a_cdn` in
[server/tests/test_browser_new_ui.py] keeps it that way. Measured on a host with no
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
[server/tests/test_browser_new_ui.py], including
`test_nothing_is_fetched_from_a_cdn`. Renderer selection is implemented in
[server/src/filemill/ui/adapters/app-http.js].

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

Follow the [root tracker rules] and the [shared contributor guide]. Validate and commit the
implementation, rebase and merge, then move the issue to Completed / Accepted
with `[ ]`. Completion is not user acceptance. Update affected documentation
with the implementation.

[the served UI tests]: tests/test_browser_new_ui.py
[browser-wait guard]: tests/test_browser_waits.py
[outline history regression]: tests/test_browser_new_ui.py
[root edition/renderer table]: ../README.md#choose-an-edition
[shared contributor guide]: ../CONTRIBUTING.md
[root README]: ../README.md
[server/src/filemill/app.py]: src/filemill/app.py
[server/src/filemill/ui/adapters/app-http.js]: ../ui/adapters/app-http.js
[server/pyproject.toml]: pyproject.toml
[server/src/filemill/paths.py]: src/filemill/paths.py
[SECURITY.md]: ../SECURITY.md
[the replacement decision]: ../docs/adr/0090-revision-checked-file-replacement.md
[ADR 0088]: ../docs/adr/0088-remove-named-mount-and-alternate-shell-routes.md
[service worker]: src/filemill/static/sw.js
[server/src/filemill/ui/adapters/server-status.js]: ../ui/adapters/server-status.js
[ADR 0089]: ../docs/adr/0089-an-offline-server-shows-older-copies-with-an-indicator.md
[server/tests/test_browser_new_ui.py]: tests/test_browser_new_ui.py
[root tracker rules]: ../TASKS.md#rules
[server/src/filemill/ui/]: src/filemill/ui/
[server/src/filemill/static/]: src/filemill/static/
[server/]: ./
[pytest.ini]: ../pytest.ini
[conftest.py]: ../conftest.py
[server/tests/test_pytest_config.py]: tests/test_pytest_config.py
[server/tests/test_browser_keyboard.py]: tests/test_browser_keyboard.py
