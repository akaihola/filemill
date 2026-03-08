# Issues

Each issue has an explicit **Status** field: `open`, `in-progress`, or `closed`.

When closing an issue, set `**Status:** closed` and add a `**Closed:** YYYY-MM-DD` date.
**Closed issues are pruned from this file 90 days after their closed date.** Remove both
the issue block here and the corresponding `[x]` line in TASKS.md at that point.

---

## #38 – CORS headers on `/w/` routes for cross-origin image embedding

**Type:** feature
**Status:** closed
**Closed:** 2026-03-08
**Prune after:** 2026-06-06

Other sites need to embed images (and other static assets) served by pykofinder
via `/w/` URLs inside `<img>` tags or `fetch()` calls. Without CORS headers the
browser blocks these cross-origin requests.

**Scope:** `/w/{path:path}` only – all other routes are unaffected.

**Implementation:**

- `web_static()` – add `Access-Control-Allow-Origin: *`,
  `Access-Control-Allow-Methods: GET, OPTIONS`, and
  `Access-Control-Allow-Headers: *` to the `FileResponse`.
- Add an `OPTIONS /w/{path:path}` route so browsers can complete preflight
  checks (needed for `fetch()` requests and `<img crossorigin>`).

---

## #37 – Browser column-survival regression must use the real keyboard flow

**Type:** test
**Status:** closed
**Closed:** 2026-03-07
**Prune after:** 2026-06-05

The first browser regression for the folder-column survival bug still used mouse
clicks for opening the folder and file. That misses the actual keyboard-only flow
that previously broke: `ArrowDown` → `ArrowRight` into folder → `ArrowDown` to
file → `ArrowRight` to preview → `ArrowLeft` back out → `ArrowRight` back in →
`ArrowDown`/`ArrowRight` to preview again.

The repo test should exercise that exact sequence so it fails if keyboard focus,
selection restoration, or sentinel cleanup regresses again.

---

## #36 – Add browser regression test for column survival after ArrowLeft/ArrowRight

**Type:** test
**Status:** closed
**Closed:** 2026-03-07
**Prune after:** 2026-06-05

The keyboard-navigation regressions fixed in `styles.py` included a DOM-order bug
where stale sentinel nodes caused a parent folder column to disappear after this flow:
open folder → open file preview → `ArrowLeft` → re-enter folder → open file preview.

The repository should keep a browser-level regression test for that exact scenario,
not just string-based assertions on `COLUMN_JS`.

**Goal:**

- Add a real browser test that reproduces the above sequence and asserts the
  folder column remains present while the preview updates.
- Keep it in the same optional Playwright test module as the ArrowLeft URL test.

---

## #35 – Add browser regression test for ArrowLeft URL sync

**Type:** test
**Status:** closed
**Closed:** 2026-03-07
**Prune after:** 2026-06-05

The `ArrowLeft` URL-sync bug was fixed with string-level regression tests and an
ad-hoc Playwright script, but the repository still lacks a browser-level test that
proves the real address bar changes correctly during keyboard navigation.

**Goal:**

- Add a pytest browser test that opens a real pykofinder page, navigates into a
  folder and file, presses `ArrowLeft`, and asserts that `page.url` moves back to
  the parent item and then to `/f/` at root.
- Skip automatically when Playwright or `PLAYWRIGHT_BROWSERS_PATH` is unavailable.

**Planned implementation:**

- Add `tests/test_browser_keyboard.py` using `playwright.sync_api`.
- Start a temporary uvicorn server in a background process against a temp ROOT.
- Use pytest skip guards so the main suite stays reliable on environments without
  Playwright.
- Document how to run the browser test with the pinned Playwright version.

---

## #34 – ArrowLeft must update the browser URL

**Type:** bug
**Status:** closed
**Closed:** 2026-03-07
**Prune after:** 2026-06-05

After navigating into a folder or file with the keyboard, pressing `ArrowLeft`
closes columns and/or clears the preview, but the browser URL stays at the
previous deeper path. Refreshing after `ArrowLeft` restores the wrong location,
and the address bar no longer matches the visible Finder state.

**Expected behaviour:**

- If `ArrowLeft` exits a child column, the URL should move back to the selected
  item in the parent column.
- If `ArrowLeft` is pressed in the root column, the URL should reset to `/f/`.

**Planned fix:**

- Add a small URL-sync helper in `styles.py` `COLUMN_JS` that can derive
  `path`/`vpath` from a selected entry's `hx-get` URL and call
  `history.pushState()`.
- Call that helper from the `ArrowLeft` handler after focus/selection has moved
  left.
- Reset the URL to `/f/` when `ArrowLeft` clears the root-column selection.

**Tests to add:**

- `test_arrow_left_updates_url_from_parent_selection`
- `test_arrow_left_at_root_resets_url`

---

## #33 – PWA: make pykofinder installable as a Progressive Web App

**Type:** feature
**Status:** closed
**Closed:** 2026-03-07
**Prune after:** 2026-06-05

Add the three ingredients that browsers require for an "Add to Home Screen" / install
prompt:

1. **Web App Manifest** (`/manifest.json`) – name, start URL (`/f/`), standalone display
   mode, theme colour, and icon entries (192 × 192 PNG, 512 × 512 PNG, SVG).
2. **Service worker** (`/sw.js`) – stale-while-revalidate for the app shell and static
   assets; network-only for dynamic HTMX partials (`/click`, `/restore`, `/raw`, `/vpage`,
   `/sse/*`).
3. **Head tags in every shell page** – `<link rel="manifest">`, `<meta name="theme-color">`,
   viewport meta, Apple-touch-icon link, and an inline SW registration snippet.

**Implementation** (`src/pykofinder/`):

1. `static/manifest.json` – manifest document.
2. `static/sw.js` – service worker.
3. `static/icons/icon.svg`, `icon-192.png`, `icon-512.png` – bundled icons (PNGs
   generated programmatically via Python `struct` + `zlib`; no new runtime deps).
4. `app.py` – three new routes (`/manifest.json`, `/sw.js`, `/icons/{name}`); `_shell_html()`
   gains seven new head elements; `_reorder_routes()` now also prioritises the new routes.
5. `tests/test_pwa.py` – 20 tests covering all routes and head-tag requirements.

---

## #30 – JSON VFS preview shows "not yet implemented" stub

**Type:** bug
**Status:** closed
**Closed:** 2026-03-06

`.json` files are registered as VFS provider entries but both `render_preview` and the
`restore()` guard prevent any real content from appearing:

1. `json_provider.py` `render_preview` returns a literal stub string
   `"JSON VFS not yet implemented."` instead of rendering the file content.
2. `app.py` `restore()` has an `if current_vpath:` guard around the
   `render_preview` call in the "no children" branch. For a JSON file at
   root vpath (`""`) this guard evaluates to `False`, so the preview is
   silently skipped and the pane remains blank.

**Fix:**

- Implement `render_preview` in `json_provider.py` to read the file, pretty-print
  valid JSON, and render it with Pygments syntax highlighting (same `"friendly"`
  style used everywhere else). Fall back to raw `<pre>` if Pygments is unavailable;
  show malformed JSON as raw text.
- Remove the `if current_vpath:` guard in `restore()` so that VFS providers with
  no navigable children (like the JSON provider) still get their preview rendered
  even at root vpath.

**Tests added:**

- `test_click_json_file_renders_json_not_stub` – clicking a `.json` file returns
  formatted JSON content, not the stub message.
- `test_restore_json_file_shows_json_preview` – `/restore` for a `.json` file
  includes JSON content in the preview pane.

**Prune after:** 2026-06-04

---

## #26 – Deep-link broken for zone-2 sub-paths; HTMX not re-initialised after restore

**Type:** bug
**Status:** closed
**Closed:** 2026-03-06

Two related deep-link bugs triggered when navigating to a URL whose `?path=`
parameter points into a zone-2 symlink tree (a directory symlinked into ROOT):

1. **Missing intermediate columns** – `restore()` used `parts = [p.name]` for
   any zone-2 path, losing all path components above the leaf name. For example
   `/home/agent/my-knowledge/docs` produced `parts = ["docs"]`, so only the ROOT
   column was generated instead of ROOT → bookmark → docs.

2. **Clicks in restored columns do nothing** – HTMX 1.9.x has no
   `MutationObserver`. When `_deepNavigate` replaced `#app-shell` via
   `outerHTML`, HTMX never saw the new elements; `hx-get` attributes were dead.
   Clicking any item in a restored column silently failed.

**Fix:**

- `app.py` `restore()`: on `ValueError` (zone-2 path), iterate ROOT's direct
  symlink children and find the one whose resolved target is an ancestor of `p`.
  Reconstruct `parts` as `[symlink_name, *relative_parts]` so every intermediate
  directory column is rendered.
- `styles.py` `COLUMN_JS` `_deepNavigate`: after `shell.outerHTML = html`,
  query the new `#app-shell` and call `htmx.process(newShell)` to initialise all
  HTMX attributes in the freshly-injected HTML.

**Tests added:**

- `test_restore_zone2_deep_path_shows_all_columns` – verifies col-0, col-1, col-2
  are all present in the restore response for a zone-2 sub-directory.
- `test_deep_navigate_calls_htmx_process` – verifies `htmx.process` appears
  inside `_deepNavigate` in `COLUMN_JS`.

**Prune after:** 2026-06-04

---

## #25 – Dotfile visibility toggle in `<nav>`

**Type:** feature / UX
**Status:** closed
**Closed:** 2026-03-06

Add a hidden-dotfile visibility toggle button (`.*`) to the `<nav id="breadcrumb">`
bar. By default, entries whose names begin with `.` are excluded from column views.
The toggle reveals them (with a slight opacity to visually distinguish them from
regular entries) and persists the preference in `localStorage`.

**Implementation sketch:**

- `columns.py`: remove the `p.name.startswith(".")` skip in `list_column()`; add
  `cls="dotfile"` to the `Li` for such entries instead. Add a `<button id="dotfiles-btn"
class="bc-toggle">.*</button>` at the end of every `render_breadcrumb()` return value.
- `styles.py`: update `#breadcrumb` to `display: flex` so the button floats right.
  Add `.column li.dotfile { display: none }` + `body.show-dotfiles .column li.dotfile
{ display: list-item; opacity: 0.65 }`. Add `.bc-toggle` button CSS. Add JS:
  `initDotfilesToggle()`, `_syncDotBtn()`, `toggleDotfiles()`. Wire `_syncDotBtn()`
  into `htmx:afterSettle` and `initDotfilesToggle()` into `DOMContentLoaded`.

**Implemented:** `columns.py` – `render_breadcrumb()` appends
`<button id="dotfiles-btn" class="bc-toggle" onclick="toggleDotfiles()">.*</button>`;
`list_column()` adds `cls="dotfile"` to dotfile `Li`s instead of skipping them.
`styles.py` – `#breadcrumb` changed to `display: flex`; `.bc-toggle` button CSS;
`.column li.dotfile { display: none }` + `body.show-dotfiles .column li.dotfile
{ display: list-item; opacity: 0.65 }`; JS: `_syncDotBtn()`, `toggleDotfiles()`,
`initDotfilesToggle()` (reads/writes `localStorage` key `pykofinder_show_dotfiles`);
`recalcColumnWidth()` skips hidden dotfile entries; `_syncDotBtn()` wired into
`htmx:afterSettle`; `initDotfilesToggle()` wired into `DOMContentLoaded`.
**Prune after:** 2026-06-04

---

## #1 – Add PNG and JPEG preview

**Type:** feature
**Status:** closed
**Closed:** 2026-03-01

Show inline image preview for `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, and `.svg` files
when clicked in the column view. Render as a plain `<img>` tag (served via the existing
`/raw` endpoint) with `max-width: 100%` and `max-height: 100%` inside the preview pane,
and a subtle checkerboard background for transparency.

**Implemented:** `preview.py` (`IMAGE_EXTS` constant + `_preview_image()`), `styles.py`
(`.preview-image` CSS), `columns.py` (`🖼` icon for image extensions).
**Prune after:** 2026-05-30

---

## #2 – Show full filename in tooltip when truncated

**Type:** UX / bug
**Status:** closed
**Closed:** 2026-03-01

Column entries are fixed-width and long filenames are clipped with CSS `text-overflow:
ellipsis`. When a filename is clipped the user has no way to read it. Add a `title`
attribute to every `<li>` (or its inner `<span>`) containing the full filename so the
browser shows a native tooltip on hover.

**Implemented:** `columns.py` – added `title=p.name` to both `A(...)` calls in
`list_column()` (directory branch and file branch).
**Prune after:** 2026-05-30

---

## #3 – Auto-adjust column width to fit longest filename

**Type:** UX / feature
**Status:** closed
**Closed:** 2026-03-01
**Prune after:** 2026-05-30

Column width is currently hard-coded to 220 px. Instead, compute the width from the
longest filename in the currently-visible columns (all columns share the same width),
subject to two constraints:

- **minimum** – wide enough to show the shortest useful name without truncation
- **maximum** – narrow enough that the total width of all open columns plus the preview
  pane still fits horizontally in the viewport without horizontal scroll

The width should be recalculated whenever a new column is opened or closed.

---

## #9 – Preview pane always at least 1/3 viewport width

**Type:** UX / layout
**Status:** closed
**Closed:** 2026-03-01
**Prune after:** 2026-05-30

The preview pane had a fixed `min-width: 320px` regardless of viewport size. On wide
screens this let the file-column strip crowd out the preview. The preview should always
occupy at least one-third of the viewport, and the column-width budget should shrink
accordingly.

**Implemented:** `styles.py` – `#preview min-width` changed from `320px` to `33.333vw`;
`COLUMN_JS` `PREVIEW_MIN` constant changed from `320` to
`Math.round(window.innerWidth / 3)`.

---

## #4 – Zoom button: expand preview to full page width

**Type:** feature
**Status:** closed
**Closed:** 2026-03-01

Add a small toggle button (e.g. ⛶ / ✕ or a magnifier icon) in the top-right corner of
the preview pane. When activated:

- the file-column area is hidden (`display: none` or slid out)
- the preview pane expands to fill the full viewport width
- the button icon changes to indicate "zoom out / restore"

When the button is clicked again the layout reverts to the normal columns + preview split.
The zoom state should survive HTMX partial swaps (i.e. re-opening a file while zoomed
keeps the pane zoomed).

**Implemented:** `styles.py` – `#zoom-btn` CSS (fixed-position button), `body.zoomed`
CSS rules (hides `.column`, expands `#preview` to `100vw` with `box-sizing: border-box`),
`initZoomButton()` JS function (injects button into `document.body` outside `#preview`
so HTMX swaps can't remove it), called from `DOMContentLoaded` listener. `.preview-md`
gets `margin: 0 auto` so it centres within the full-width pane.
**Prune after:** 2026-05-30

---

## #5 – URL reflects current path; deep-link navigation

**Type:** feature
**Status:** closed
**Closed:** 2026-03-05
**Prune after:** 2026-06-03

The browser URL should stay in sync with the currently selected file or directory as the
user navigates the column view, and pasting or opening a URL should restore the exact same
view.

**URL scheme** – encode the selected path as a URL-encoded subpath after the origin, e.g.:

```
https://gogo.crane-boa.ts.net:8445/browse/paivi/documents/reports/2025/budget.pdf
```

or as a query parameter if a subpath conflicts with existing routes:

```
https://gogo.crane-boa.ts.net:8445/?path=reports/2025/budget.pdf
```

**Sync while navigating** – after every successful `/click` response, call
`history.pushState()` (or `replaceState` for intermediate directory columns) to update the
browser URL without a full page reload. No server round-trip needed for the URL update
itself.

**Deep-link on load** – when the page is loaded with a non-root path, the server (or
client-side JS on `DOMContentLoaded`) should:

1. Split the path into its components (e.g. `reports`, `2025`, `budget.pdf`).
2. Sequentially open one column per component, exactly as if the user had clicked each
   entry.
3. Scroll the column strip to show the rightmost column and, if the final component is a
   file, render its preview.

**Edge cases to handle:**

- Path no longer exists → show an error column or fall back to root.
- Path escapes the configured root → reject (same `_resolve_safe` logic).
- Browser back/forward buttons → listen to `popstate` and re-render columns to match the
  URL that was popped.

**foam-web approach:** foam-web achieves this naturally via multi-page WSGI routing –
every file and directory has its own stable URL (`/<dir>/` and `/<dir>/<file>`). There
is no `pushState()` needed because the browser handles full page loads. For pykofinder's
SPA model, calling `history.pushState({}, "", newUrl)` inside the HTMX `htmx:afterSwap`
event handler after every `/click` response is the direct equivalent.

---

## #6 – Auto-reload: code changes restart server; content changes refresh browser

**Type:** developer experience
**Status:** closed
**Closed:** 2026-03-05
**Prune after:** 2026-06-03

Two related but distinct reload mechanisms are both missing:

**Part A – Server restart on code change (partially addressed by `--live`)**

When running in development, the server should automatically restart whenever a source
file under `src/pykofinder/` is modified. The existing CLI already has a `--live` flag
that passes `reload=True` to uvicorn. The service unit should be updated (or a separate
dev-launch script/`Makefile` target added) to start with `--live`.

**Part B – Browser refresh on content change (not yet addressed)**

When any document under the served root is saved (`.md`, `.txt`, images, etc.), the
browser tab should automatically refresh without requiring a manual `F5`. This is
independent of code changes – it aids content editing workflows.

**foam-web implementation of Part B** (`src/foam_web/serve.py` + `src/foam_web/styles.py`):

- `livereload.Server` wraps the WSGI app; `server.watch(str(root / "**/*.md"))` is called
  to register a glob watcher.
- Every rendered HTML page has `<script src="/livereload.js?port={port}&mindelay=10"></script>`
  injected (the `livereload` library serves this script automatically).
- On file save, the livereload WebSocket pushes a reload event to the browser tab.
- After a server restart (via `hupper`), a background thread (`_delayed_reload`) waits
  1 second then appends a fake change to `server.watcher._changes` to trigger a
  browser refresh after the new process is ready.

**pykofinder sketch for Part B:**

- Add [`watchfiles`](https://pypi.org/project/watchfiles/) (async, no extra process) or
  use uvicorn's built-in file-change signal.
- Serve a small SSE endpoint (e.g. `GET /sse/reload`) that streams an event whenever the
  root directory tree changes.
- Inject `<script>` into the base page that connects to the SSE endpoint and calls
  `location.reload()` on receipt.
- Gate the watcher behind `--live` so production deployments are unaffected.

---

## #7 – Preview unrecognised text files raw

**Type:** feature
**Status:** closed
**Closed:** 2026-03-05
**Prune after:** 2026-06-03

Files whose extension is not explicitly handled (no Markdown renderer, no Office
converter, no PDF viewer, no image tag) but which are valid UTF-8 text should still be
shown in the preview pane as plain text – wrapped in a `<pre>` block – rather than
displaying "No preview available."

Implementation sketch:

1. After all existing extension checks in `render_preview()`, add a final fallback that
   attempts to read the file as UTF-8 (up to a reasonable cap, e.g. 256 KB).
2. If decoding succeeds, return the content inside a `<pre class="preview-raw">` element
   (HTML-escaped).
3. If decoding raises `UnicodeDecodeError` (binary file), fall through to the existing
   "No preview available" message.
4. Add a `.preview-raw` CSS rule (monospace font, wrapping, subtle background) to
   `styles.py`.

**foam-web approach** (`src/foam_web/app.py` + `src/foam_web/views.py`): foam-web's
`serve_raw()` returns `None` for files with no recognised lexer; the WSGI handler then
falls back to reading the raw bytes and returning them as `Content-Type: text/plain;
charset=utf-8` for the browser to display. This is simpler than a styled `<pre>` but
ensures the content is never silently swallowed. For pykofinder the styled `<pre>` inside
the preview pane is the right target since it keeps the two-panel layout intact.

**Implemented:** `preview.py` – UTF-8 fallback in `render_preview()` else-branch (≤256 KB
size cap, `UnicodeDecodeError` falls through); `styles.py` – `.preview-raw` CSS rule.

---

## #10 – Selected directories/files must stay highlighted

**Type:** UX / bug
**Status:** closed
**Closed:** 2026-03-05
**Prune after:** 2026-06-03

When navigating the column view, the selected item in each column does not retain a
highlighted background after the HTMX partial-swap completes. Two distinct cases must
both be handled:

1. **Directory column entry** – a directory whose contents are currently displayed in the
   next column to the right must have a highlighted (selected) background colour,
   matching the macOS Finder column-view behaviour.
2. **File column entry** – the file whose content is currently shown in the preview pane
   must have a highlighted background colour.

The highlight must persist across subsequent clicks (opening deeper sub-directories or
switching the preview to a different file) and must not be lost by HTMX swaps.

**Implementation sketch:**

- Add a CSS rule for a `selected` class (or `aria-selected="true"` attribute) on `<li>`
  elements that gives them a distinct background (e.g. the accent blue used in Finder).
- After each `/click` response, the server should mark the clicked item as selected in
  the returned HTML _and_ strip the `selected` state from any sibling items in the same
  column (or the client JS should do so via an `hx-on::after-request` handler that walks
  up to the parent `<ul>` and clears siblings before adding the class to the target).
- Because multiple columns can be open simultaneously (one directory per column), the
  highlight must apply independently per column – the selected item in column N is the
  one that opened column N+1, and the selected file in the rightmost column is the one
  whose preview is showing.

---

## #12 – .desktop link file support

**Type:** feature
**Status:** closed
**Closed:** 2026-03-05

Column view displays a `🔗` icon for `.desktop` files. Clicking a `.desktop` entry
opens its destination URL directly in a new browser tab via a `/open-link` redirect
route – never via HTMX (no `#preview` update). The preview pane shows a card with the
entry name, an optional remote icon (`http://` / `https://` only), a comment line, the
raw URL as a link, and an "Open →" button that also uses `/open-link`.

A `~/menu/` root directory of workspace symlinks and `.desktop` hyperlinks was created
and set as the service root via a systemd drop-in (`pykofinder.service.d/root.conf`).
The NixOS config was updated for persistence.

**Implemented:**

- `app.py`: `_parse_desktop_url()`, `GET /open-link`
- `columns.py`: `🔗` icon, `.desktop`-specific `<a target="_blank">` branch (no HTMX)
- `preview.py`: `_preview_desktop()`, `.desktop` dispatch added to `render_preview()`

**Prune after:** 2026-06-03

---

## #11 – Symlinks in ROOT denied with "Access denied."

**Type:** bug
**Status:** closed
**Closed:** 2026-03-05

`_resolve_safe` called `Path.resolve()` (which follows symlinks) _before_ the
containment check, so a symlink entry such as `~/menu/paivi → /home/agent/paivi`
resolved to `/home/agent/paivi` and then failed the `relative_to(ROOT)` guard.
Additionally, once a symlink _was_ followed (e.g. the user clicked into it), every
subsequent path inside that subtree (e.g. `/home/agent/paivi/documents`) also failed
because it was not lexically under ROOT.

**Fix:** zone-based containment check operating on the _fully resolved_ path:

- **Zone 1** – resolved path is within ROOT (all real files/dirs).
- **Zone 2** – resolved path is within the resolved target of any _direct_ symlink
  child of ROOT. This lets directory symlinks placed in ROOT act as bookmarks whose
  subtrees are fully browsable.

Symlinks _within_ a bookmark subtree whose target escapes all allowed zones are
still denied, as are classic `..`-traversal attacks (defeated by `resolve()`).

`_resolve_safe` gained an optional `root` parameter so tests can inject a
temporary tree without touching the module-level `ROOT` global.

**Files changed:** `src/pykofinder/app.py`, `pyproject.toml` (added `pytest` dev
dep + `[tool.pytest.ini_options]`), `tests/__init__.py`, `tests/test_resolve_safe.py`
(16 cases: zone-1 access, zone-2 bookmark access, safe nested symlinks, escaped
nested symlinks, traversal attacks, URL-encoding, startswith prefix-collision).
**Prune after:** 2026-06-03

---

## #8 – Move project context to AGENTS.md for pi auto-loading

**Type:** chore / developer experience
**Status:** closed
**Closed:** 2026-03-01

Pi Coding Agent auto-loads `AGENTS.md` (walking up from cwd), but does **not** auto-load
`.claude/CLAUDE.md` (a Claude Code convention). The deployment and project context that
lived in `.claude/CLAUDE.md` was therefore invisible to pi at session start.

**Fix:** moved content to `./AGENTS.md` (gitignored via `.gitignore`); `.claude/CLAUDE.md`
now contains only `@../AGENTS.md` so Claude Code still picks it up via its reference
syntax.

**Files changed:** `AGENTS.md` (new, gitignored), `.claude/CLAUDE.md`, `.gitignore`.
**Prune after:** 2026-05-30

---

## #13 – Breadcrumb navigation

**Type:** UX / feature
**Status:** closed
**Closed:** 2026-03-05
**Prune after:** 2026-06-03

Render a `~ / dir / subdir / file` breadcrumb trail above the column strip so the user
can see their current location.

**Implemented:**

- `columns.py`: `render_breadcrumb(path, root) -> str` – returns `<nav id="breadcrumb">`
  HTML with `~` root, `/`-separated segments (HTML-escaped via `html.escape()`);
  `initial_columns()` now returns `#app-shell` wrapper div containing the breadcrumb nav
  above the `#finder` div.
- `app.py`: `click` handler returns OOB `<nav id="breadcrumb" hx-swap-oob="true">` in
  both the directory case (tuple return) and the file case (appended to `NotStr`).
- `styles.py`: `#app-shell` flex column container, `#breadcrumb` strip styles,
  `.bc-root`/`.bc-seg`/`.bc-sep` classes; `#finder` changed from `height: 100vh` to
  `flex: 1; min-height: 0`; `body` gained `height: 100vh`.

---

## #14 – Source code file syntax highlighting

**Type:** feature
**Status:** closed
**Closed:** 2026-03-05
**Prune after:** 2026-06-03

Files with code extensions (`.py`, `.js`, `.ts`, `.sh`, `.yaml`, `.toml`, `.rs`, `.go`,
`.c`, `.cpp`, `.json`, `.html`, `.css`, etc.) should render with Pygments syntax
highlighting in the preview pane rather than displaying "No preview available."
The Pygments `"friendly"` style should be used for visual consistency with foam-web.

**foam-web implementation** (`src/foam_web/views.py` lines 64–81 `serve_raw()`,
`src/foam_web/styles.py` line 8):

```python
# styles.py
FORMATTER = HtmlFormatter(style="friendly", nowrap=False)

# views.py – serve_raw()
try:
    lexer = get_lexer_by_name(full.suffix.lstrip("."))
except Exception:
    try:
        lexer = guess_lexer(full.read_text(encoding="utf-8"))
    except Exception:
        lexer = None
if lexer:
    body = highlight(full.read_text(encoding="utf-8"), lexer, FORMATTER)
    return render_page(title=full.name, nav=..., body=body)
return None  # falls back to raw bytes
```

Key details:

- Extension lookup (`get_lexer_by_name`) is tried first; `guess_lexer` is the fallback.
- `HtmlFormatter(style="friendly", nowrap=False)` wraps output in
  `<div class="highlight"><pre>` giving a visually distinct code block.
- The `"friendly"` Pygments theme is a warm light palette (soft greens/blues).
- Pygments' CSS for the chosen style should be injected once into the page via
  `HtmlFormatter(style="friendly").get_style_defs(".highlight")`.

**pykofinder sketch:**

- In `render_preview()` (`preview.py`), after all existing extension checks and before
  the final "No preview available" fallback, add a Pygments branch:
  1. Try `get_lexer_by_name(ext.lstrip("."))`.
  2. On failure, try `guess_lexer(content)`.
  3. On success, call `highlight(content, lexer, HtmlFormatter(style="friendly", nowrap=False))`.
  4. Wrap in `<div class="preview-code">` with padding.
  5. Gate on a file-size cap (~512 KB) to avoid memory issues with large generated files.
- In `styles.py`, add `HtmlFormatter(style="friendly").get_style_defs(".highlight")` to
  the page `<style>` block (Pygments is already a transitive dep; add it explicitly to
  `pyproject.toml` if needed).
- This branch should run **before** the raw-text fallback (#7) so code files get colours;
  unrecognised UTF-8 files fall through to plain `<pre>`.

---

## #17 – Fix hanging SSE test (`test_sse_reload_exists_with_live_mode`)

**Type:** bug / testing
**Status:** closed
**Closed:** 2026-03-05
**Prune after:** 2026-06-03

`tests/test_app.py::test_sse_reload_exists_with_live_mode` hangs indefinitely
because it calls `TestClient.get("/sse/reload", timeout=0.5)` against an infinite
SSE streaming endpoint.

**Why the timeout doesn't help:**
`starlette.testclient.TestClient` runs the ASGI app in a background thread and
uses `requests` as its HTTP transport. The `timeout=0.5` on `.get()` is a _read_
timeout that resets each time a chunk arrives. The `/sse/reload` endpoint emits
`": keepalive\n\n"` pings continuously, so the read-timeout window keeps refreshing
and the call never returns.

**Fix:**
Replace the live-HTTP approach with one that doesn't block on the stream:

Option A (preferred) – assert the _route is registered_ rather than making a
request, then check the response status in a separate focused test that streams
only the first line:

```python
def test_sse_reload_exists_with_live_mode(tmp_root, monkeypatch):
    import pykofinder.app as app_module
    monkeypatch.setattr(app_module, "LIVE_MODE", True)
    from starlette.testclient import TestClient
    c = TestClient(app_module.app, raise_server_exceptions=False)
    with c.stream("GET", "/sse/reload") as resp:
        assert resp.status_code != 404
        # Read only the first chunk then bail out
        next(resp.iter_lines())
```

Option B – check that the route exists on `app.routes` without making any HTTP
request at all, and rely on a separate integration test that patches the watchfiles
generator to yield one event then stop.

A second hanging test was also found in `tests/test_preview.py`:
`test_large_text_file_shows_unsupported` created a 256 KB file (within Pygments'
512 KB syntax-highlight limit) with a `.log` extension. `get_lexer_by_name("log")`
raised `ClassNotFound`, so `guess_lexer()` was called on 256 KB of repeated `'x'`
bytes — Pygments heuristics on uniform binary-ish data hang indefinitely. Fix: size
the test file to 512 KB + 1 so it exceeds both the Pygments limit and the raw-text
limit. **Fixed** 2026-03-06 (`f.write_bytes(b"x" * (512 * 1024 + 1))`).

**Discovered:** 2026-03-06 – these tests caused the Pi "Pykofinder hackathon" session
to stall for ~3.5 hours when `uv run pytest` was run as a bash tool call with no
shell-level timeout.

---

## #15 – Keyboard navigation

**Type:** UX / accessibility
**Status:** closed
**Closed:** 2026-03-05
**Prune after:** 2026-06-03

Users should be able to navigate the column view using the keyboard without reaching for
the mouse – essential for power users and accessibility.

**Target behaviour (macOS Finder column-view model):**

| Key       | Action                                                                    |
| --------- | ------------------------------------------------------------------------- |
| `↑` / `↓` | Move selection up/down within the focused column                          |
| `→`       | Open selected directory (add next column) or preview selected file        |
| `←`       | Move focus back to the parent column and close child columns to the right |
| `Enter`   | Same as `→`                                                               |
| `Escape`  | Clear selection / collapse to root                                        |

**foam-web approach:** foam-web gets keyboard navigation for free because it uses
full-page navigation – standard browser Tab/Enter/Back-Forward all work without any
custom JS. For pykofinder's SPA column view, custom `keydown` handlers are needed.

**pykofinder sketch:**

- Add a `keydown` listener on `document` in the column JS block (`styles.py`
  `COLUMN_JS`).
- Track the "focused column index" and "selected item within that column" in JS state.
- `↑`/`↓`: move selection within the current column's `<ul>` and trigger an HTMX
  request (or simulate a click) on the new `<li>`.
- `→`/`Enter`: fire the HTMX request for the currently selected `<li>` (identical to a
  mouse click).
- `←`: remove the rightmost column(s) until focus is at the previous column; restore the
  previously selected item there.
- Sync keyboard focus with the selected-item highlight from issue #10.
- Ensure `aria-selected` attributes are updated for screen-reader compatibility.

---

## #16 – Bind address CLI option (`--bind` / `SERVE_BIND` env var)

**Type:** feature / developer experience
**Status:** closed
**Closed:** 2026-03-05
**Prune after:** 2026-06-03

---

## #18 – Virtual-FS navigation and view-format switching (SQLite + extensible registry)

**Type:** feature
**Status:** closed
**Closed:** 2026-03-05
**Prune after:** 2026-06-03

**Implemented:**

- `src/pykofinder/vfs.py` – `VFSEntry`, `VFSProvider` (Protocol), `VFSRegistry`,
  `REGISTRY` singleton, `is_vfs_file()`, `_truncate()`
- `src/pykofinder/providers/__init__.py` – package marker
- `src/pykofinder/providers/sqlite.py` – `SQLiteProvider` with schema/table/row
  enumeration, row-key derivation (PK → unique col → rowid), spreadsheet preview
  (paginated), KV row-detail preview, BLOB handling
- `src/pykofinder/providers/csv_provider.py` – stub (`default_fmt="spreadsheet"`)
- `src/pykofinder/providers/json_provider.py` – stub (`default_fmt="formatted"`)
- `src/pykofinder/columns.py` – `list_vfs_column()`, `🗄️` icon for `.db`,
  VFS-file routing in `list_column()`, `vpath` param in `render_breadcrumb()`
- `src/pykofinder/app.py` – `/click` VFS dispatch (`vpath`, `fmt` params),
  `_make_bc_oob()`, `_build_prune_js()` helpers, `/vpage` endpoint
- `src/pykofinder/styles.py` – VFS/DB CSS, format-persistence JS (localStorage)
- `tests/test_vfs.py`, `tests/test_providers_sqlite.py`,
  `tests/test_integration_vfs.py` – new test files

### Summary

Two interlocking features:

1. **Virtual filesystem (VFS) navigation** – certain file types (starting with SQLite
   `.db`) behave like navigable directories: their internal structure (schemas, tables,
   rows) is exposed as additional Finder columns rather than a static preview.
2. **View-format switching** – a general mechanism for toggling between alternate
   renderings of an item (e.g. spreadsheet vs row-folders for a DB table, spreadsheet
   vs raw for CSV, formatted vs raw for JSON). The toggle button lives in the
   currently-active view container (column header when in folder/column mode; preview
   header when in preview mode).

### New modules

| Module                                      | Responsibility                                                                                 |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `src/pykofinder/vfs.py`                     | `VFSEntry` dataclass; `VFSProvider` protocol; `VFSRegistry` singleton; format-default registry |
| `src/pykofinder/providers/__init__.py`      | Package marker                                                                                 |
| `src/pykofinder/providers/sqlite.py`        | Concrete `VFSProvider` for `.db`                                                               |
| `src/pykofinder/providers/csv_provider.py`  | Stub (spreadsheet vs raw)                                                                      |
| `src/pykofinder/providers/json_provider.py` | Stub (formatted vs raw)                                                                        |

### URL / routing changes

**`/click` extended params** (backward-compatible):

| Param   | Meaning                                                                              |
| ------- | ------------------------------------------------------------------------------------ |
| `vpath` | Virtual path within the file at `path`, slash-separated (e.g. `users` or `users/42`) |
| `fmt`   | Explicit view-format override; if absent, resolved from localStorage via JS          |

**New endpoint `/vpage`** – paginated table rows:
`GET /vpage?path=/abs/foo.db&vpath=users&page=1&limit=1000`
Returns an HTMX fragment: `<table>` + pagination controls swapped into `#preview`.

### SQLite VFS – three navigation levels

- **Level 0** (clicking `.db` file): tables column (skip schema level when only `main`;
  show schema folders if multiple schemas exist)
- **Level 1** (clicking a table), two formats:
  - `folders` (default): new column listing rows as folder items; toggle `[📋 Rows | 📊 Spreadsheet]` in column header
  - `spreadsheet`: paginated `<table>` in preview pane; toggle `[📋 Rows | 📊 Spreadsheet]` in preview header
- **Level 2** (clicking a row): key-value `<table>` in preview; no format toggle

### Row-key derivation (priority order)

1. Single-column primary key → its value
2. Multi-column primary key → `col1=val1, col2=val2`
3. No PK, first column is unique → first column value
4. Otherwise → `row_N` (1-indexed)

Always truncate display label to 60 chars + `…`.

### BLOB / large-string handling

- **BLOBs**: `⟨binary data, N bytes⟩`
- **Strings > 200 chars**: truncated in labels/spreadsheet; full value shown in KV detail

### Format persistence – localStorage (client-side)

Two-tier lookup injected as `&fmt=…` into HTMX requests via `htmx:configRequest`:

```
vfmt_file_{abs_path}::{vpath}   →  per-file + vpath (most specific)
vfmt_type_{.ext}                →  type-level fallback
built-in default                →  .db → folders; .csv → spreadsheet; .json → formatted
```

Written to localStorage when user clicks a format toggle button.

### Icons

| Context       | Icon |
| ------------- | ---- |
| `.db` file    | 🗄️   |
| Schema folder | 📁   |
| Table folder  | 🗃️   |
| Row folder    | 📋   |

### Pagination

- Default page size: 1 000 rows
- Controls: `← Prev  Page N of M  Next →` as HTMX links at bottom of `<table>`, target `#preview`

### Test plan

- `tests/test_vfs.py` – registry lookup, format-default resolution
- `tests/test_providers_sqlite.py` – schema/table/row enumeration, PK fallbacks, BLOB display, pagination
- `tests/test_app.py` additions – `/click` with `vpath`, `/vpage` pagination, format toggle responses
- `tests/test_columns.py` additions – column with `fmt-bar` header

---

## #16 – Bind address CLI option / `SERVE_BIND` env var

The server is currently hard-coded to bind on `0.0.0.0` (all interfaces). Operators
should be able to bind to a specific network interface – e.g. `127.0.0.1` for
localhost-only development or a specific IP for a multi-homed host.

**foam-web implementation** (`src/foam_web/cli.py` lines 20–26):

```python
bind: Annotated[str, typer.Option("-b", "--bind", help="Address to bind to")] = \
    os.environ.get("SERVE_BIND", "0.0.0.0"),
```

`bind` is then passed as `host=bind` to `run_server()` → `Server.serve()`. Both the
short form (`-b`) and long form (`--bind`) are accepted, and the environment variable
`SERVE_BIND` allows configuration without CLI flags (useful for systemd `Environment=`
directives).

**pykofinder sketch:**

- In `cli.py`, add a `--bind` / `-b` option to the `serve()` command, defaulting to
  `os.environ.get("PYKOFINDER_BIND", "0.0.0.0")`.
- Pass it through to both `uvicorn.run()` call sites (the `reload=True` branch and the
  normal branch) as the `host=` argument.
- Update `~/.config/systemd/user/pykofinder.service` (or its drop-in) with an
  `Environment=PYKOFINDER_BIND=0.0.0.0` line so the binding is explicit and easy to
  change without editing the unit file.
- Document in `README.md` and `CONTRIBUTING.md`.

**Implemented:** `cli.py` – `--bind` / `-b` option with `PYKOFINDER_BIND` env var
fallback; `host=bind` passed to both `uvicorn.run()` call sites; `PYKOFINDER_BIND` set
in env before the reload branch.

---

## #19 – Markdown relative link normalization

**Type:** feature
**Status:** closed
**Closed:** 2026-03-06
**Prune after:** 2026-06-04

When rendering a `.md` file, relative links (e.g. `[text](notes/other.md)`) are
resolved to an absolute pykofinder URL using a three-step search:

1. Relative to the source file's directory.
2. Each ancestor directory up to and including the nearest `.git/`-containing ancestor.
3. Recursive `rglob` by basename inside that git-root ancestor.

If found: `.md` targets → `/?path=ABSOLUTE_PATH` (triggers `_deepNavigate`);
other files → `/raw?path=ABSOLUTE_PATH`. If not found: href left unchanged.

---

## #20 – Wikilink rendering (`[[PageName]]`)

**Type:** feature
**Status:** closed
**Closed:** 2026-03-06
**Prune after:** 2026-06-04

`[[PageName]]` and `[[PageName|display text]]` in `.md` files are rendered as
`<a class="wikilink" href="...">` elements. The target file is resolved with the
same three-step algorithm as #19. Unresolved wikilinks get `href="#wikilink-{name}"`.

---

## #21 – Mermaid diagram rendering

**Type:** feature
**Status:** closed
**Closed:** 2026-03-06
**Prune after:** 2026-06-04

Code fences tagged ` ```mermaid ` produce `<div class="mermaid">…</div>` instead of a
`<pre>` block. The mermaid.js CDN script is loaded in the page `<head>` and re-invoked
(`mermaid.run()`) after each HTMX swap and after each `_deepNavigate` call.

---

## #22 – Plain URL linkification

**Type:** feature
**Status:** closed
**Closed:** 2026-03-06
**Prune after:** 2026-06-04

Plain URLs in `.md` files (e.g. `https://example.com`) that are not already wrapped in
`[…](…)` Markdown link syntax are automatically turned into clickable `<a>` elements,
using `linkify-it-py` + `markdown-it-py`'s built-in linkify support.

---

## #23 – Static webserver mode `/w/` and finder mode `/f/`

**Type:** feature
**Status:** closed
**Closed:** 2026-03-06
**Prune after:** 2026-06-04

Two new URL namespaces:

- `GET /w/{relative_path}` – serves the file at `ROOT/relative_path` with the correct
  HTTP `Content-Type` (Starlette `FileResponse`). Symlinks inside ROOT are followed via
  the existing `_resolve_safe` zone logic.
- `GET /f/{relative_path}` – redirects to `/?path=ABSOLUTE_PATH` so the column finder
  opens at that file via `_deepNavigate`.

For `.html` / `.htm` files shown in the preview pane a **"🌐 View as web page"** button
is prepended, linking to the corresponding `/w/` URL (opens in a new tab).

---

## #24 – Empty SQLite table corrupts column layout

**Type:** bug
**Status:** closed
**Closed:** 2026-03-06
**Prune after:** 2026-06-04

Clicking an empty SQLite table caused the preview HTML to be injected into the column
slot instead of `#preview`, because the `/click` handler's `elif not entries:` branch
treated empty tables the same as true leaf nodes (row detail entries).

**Root cause**: table entries are rendered in `list_vfs_column` with `is_folder=True`,
so their HTMX links target `#col-{next_col}` with `outerHTML`. But the `elif not
entries:` branch returned raw preview HTML designed for `#preview` with `innerHTML`.
After HTMX placed the preview HTML into the column slot, subsequent navigation created
duplicate columns and put content in wrong places.

**Fix** (two-part):

1. `columns.py` – leaf (non-folder) VFS entries now carry `&leaf=1` in their `hx-get`
   URL, so the server knows the request targets `#preview` via `innerHTML`.
2. `app.py` – the `elif not entries:` branch now checks the `leaf` flag:
   - `leaf=True` (true leaf / row detail) → old inline behaviour.
   - `leaf=False` (empty folder, e.g. empty table) → returns a `#col-{col}` sentinel as
     the main swap target plus an OOB `#preview` update, exactly like the spreadsheet
     branch. A `_build_prune_js(col + 1)` call is inlined in the sentinel to clean up
     any stale right-hand columns.

---

## #27 – Deep-link restore does not highlight selected entries

**Type:** bug
**Status:** closed
**Closed:** 2026-03-06
**Prune after:** 2026-06-04

When navigating to a deep-link URL such as `/f/?path=/some/dir/subdir`, the
`/restore` endpoint renders all ancestor columns but never marks any entry as
`selected`. The `selected` CSS class is normally applied only by the
click-event handler in `COLUMN_JS` — so a freshly restored view always shows
columns with no item highlighted, making it impossible to see where you are.

**Root cause**: `list_column` in `columns.py` has no way to receive which entry
should be pre-selected; `/restore` in `app.py` builds each column via
`list_column(d, ROOT, col_index=i)` with no selection hint.

**Fix** (two files):

1. `columns.py` – add `selected_name: str | None = None` to `list_column`.
   When an entry's name matches `selected_name`, its `<li>` gets the
   `selected` class (combined with `dotfile` if applicable).

2. `app.py` – the `/restore` handler already has a `parts` list whose entry
   at index `i` is the child to select in column `i`. Pass
   `selected_name=parts[i] if i < len(parts) else None` to each `list_column`
   call.

---

## #28 – Direct URL to VFS file shows "No preview available" instead of table list

**Type:** bug
**Status:** closed
**Closed:** 2026-03-06
**Prune after:** 2026-06-04

When navigating to a VFS-backed file (e.g. a SQLite `.db`) by pasting its URL
directly into the browser (e.g. `/f/?path=/path/to/file.db`), the preview pane
showed _"No preview available for .db files."_ instead of the table-list column
that appears when clicking through the columns.

**Root cause:** The `/restore` endpoint renders a preview for any file it
encounters by calling `render_preview(p)` directly, without first consulting
`REGISTRY.get(p)`. Column-click navigation goes through the `/click` handler,
which correctly checks the VFS registry and dispatches to the SQLite provider.

**Fix** (`app.py` – `restore()`):

Before calling `render_preview(p)`, check `REGISTRY.get(p)`. When a provider
is found, call `provider.list_entries(p, "")` and render the result using
`list_vfs_column()` as an extra column (mirroring what `/click` does), then
leave the preview area empty. Only fall through to `render_preview()` when no
provider is registered for the file.

---

## #29 – SQLite table/row navigation not reflected in URL

**Type:** bug
**Status:** closed
**Closed:** 2026-03-06
**Prune after:** 2026-06-04

Navigating into a SQLite `.db` file via the VFS (clicking a table, then a row)
updated the column view but left the URL unchanged at
`/f/?path=/path/to/file.db`. Refreshing or sharing the URL lost the position
within the database.

**Root cause:** The URL-sync JS captured only the real filesystem `path` from
HTMX link clicks, ignoring the `vpath` query parameter that encodes the current
VFS position (table name / row key). `/restore` likewise accepted only `path`.

**Fix** (three files):

1. `styles.py` – JS:
   - `_pendingVpath` variable captures `vpath` alongside `_pendingPath` on each
     click.
   - `pushState` includes `&vpath=…` in the URL and stores `vpath` in the
     history state object.
   - `popstate` reads `vpath` from state and passes it to `_deepNavigate`.
   - `_deepNavigate(fullPath, vpath)` appends `&vpath=…` to the `/restore`
     request when `vpath` is non-empty.
   - `DOMContentLoaded` reads `vpath` from the URL and passes it to
     `_deepNavigate`.

2. `app.py` – `/restore` endpoint:
   - Accepts optional `vpath: str = ""`.
   - For VFS files, iterates through vpath segments with a `for i in
range(len(vpath_parts) + 1)` loop: at each depth, renders a VFS column
     with `selected_vpath` highlighting; when `list_entries` returns an empty
     list (leaf or empty table), renders the preview instead and breaks.

3. `columns.py` – `list_vfs_column`:
   - New `selected_vpath: str | None = None` parameter; when
     `entry.vpath == selected_vpath` the corresponding `<li>` receives
     `class="selected"`.

---

## #31 – Enhanced keyboard navigation: Home/End/PgUp/PgDn + Left/Right focus model

**Type:** feature
**Status:** closed
**Closed:** 2026-03-06
**Prune after:** 2026-06-04

Improve the column-view keyboard navigation:

- **Up/Down**: move the highlight within the currently focused column;
  when nothing is selected, Down picks the first item and Up picks the last.
- **Right**: if a column already exists to the right, move focus there
  (to the previously highlighted item, or the first item); if at the
  rightmost column, trigger navigation into the selected item (like Enter).
- **Left**: shift focus one column left **without pruning/removing any columns**.
- **Enter**: trigger navigation (unchanged).
- **Home / End**: jump to first / last visible item in the focused column.
- **PageUp / PageDown**: jump up / down by a page (column height ÷ item height).
- **Escape**: clear all selections (unchanged).

**Implementation** (`src/pykofinder/styles.py`):

Replace the keyboard navigation IIFE with a rewritten version that:

1. Maintains a `_focusedColIndex` module-level variable (within the IIFE).
2. Adds `visibleItems(col)` helper to filter out hidden dotfile `<li>`s.
3. Adds `pageSize(col, items)` helper for PgUp/PgDn calculation.
4. Adds `triggerNav(sel)` helper (extracted from old ArrowRight/Enter block).
5. Adds a second `htmx:afterSettle` listener inside the IIFE that resets
   `_focusedColIndex = cols.length - 1` after each navigation.
6. `ArrowLeft` only adjusts `_focusedColIndex` (no `.remove()` calls).
7. Handles `Home`, `End`, `PageUp`, `PageDown` cases in the `switch`.

---

## #32 – Column focus-state visual indicators (keyboard navigation)

**Type:** feature
**Status:** closed
**Closed:** 2026-03-07
**Prune after:** 2026-06-05

When using keyboard navigation, it's impossible to tell which column is
currently focused. Three distinct visual states are needed:

- **Focused column**: current bright-blue selection (most prominent).
- **Ancestor columns** (to the left): muted/dimmed highlight – shows the
  navigation path taken, clearly less prominent than the focused column.
- **Descendant columns** (to the right): very subtle "remembered" highlight –
  signals the item is queued/waiting to regain focus, but is clearly inactive.

**Implementation** (`src/pykofinder/styles.py`):

1. **CSS** – add `.col-ancestor li.selected > a` (muted steel-blue) and
   `.col-descendant li.selected > a` (very light blue-grey + matching icon
   colour) rules after the base `.column li.selected > a` rule.

2. **JS** – inside the keyboard IIFE:
   - Add `applyFocusClasses()` that stamps `.col-ancestor`, `.col-focused`,
     or `.col-descendant` on each `.column` div based on its index vs
     `focusIndex()`.
   - Expose it via a module-level `var _kbApplyFocus` placeholder so
     `_deepNavigate` can call it after replacing the app-shell.
   - Call `applyFocusClasses()` in the keyboard IIFE's `htmx:afterSettle`
     handler, in `ArrowLeft`, in `ArrowRight` (focus-move branch), and in a
     new `DOMContentLoaded` listener inside the IIFE.
   - Call `_kbApplyFocus()` in `_deepNavigate` after `recalcColumnWidth()`.
