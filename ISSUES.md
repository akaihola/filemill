# Issues

Each issue has an explicit **Status** field: `open`, `in-progress`, or `closed`.

When closing an issue, set `**Status:** closed` and add a `**Closed:** YYYY-MM-DD` date.
**Closed issues are pruned from this file 90 days after their closed date.** Remove both
the issue block here and the corresponding `[x]` line in TASKS.md at that point.

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
**Status:** open

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
**Status:** open

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
**Status:** open

Render a `~ / dir / subdir / file` breadcrumb trail above the column strip so the user
can see their current location and jump to any ancestor directory with a single click.

**foam-web implementation** (`src/foam_web/views.py` lines 37–43):

```python
def breadcrumbs(rel: Path) -> str:
    parts = ['<a href="/">~</a>']
    accum = Path()
    for p in rel.parts:
        accum = accum / p
        parts.append(f'<a href="{quote(f"/{accum}/")}">{html.escape(p)}</a>')
    return " / ".join(parts)
```

`breadcrumbs(rel)` is called from `serve_dir`, `serve_md`, and `serve_raw` and the
result is injected into a `<nav>` element rendered at the top of every page.

**pykofinder sketch:**

- Track the selected path as state in the HTMX app (already available as the `path`
  query param on every `/click` request).
- Render `<nav id="breadcrumb">` above `#columns` in the root page template
  (`app.py` / `columns.py`).
- On each `/click` response, return an `hx-swap-oob` fragment that updates `#breadcrumb`
  with the new trail; each segment is an anchor that re-issues a `/click` for that path.
- Style: `~` as root anchor → `/ seg1 / seg2 / filename`; use a soft muted colour for
  separators and full contrast for segment text.
- Once issue #5 (URL sync) is resolved the breadcrumb can also be derived client-side
  from the URL, removing the need for OOB updates.

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

## #15 – Keyboard navigation

**Type:** UX / accessibility
**Status:** open

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
