# Issues

Each issue has an explicit **Status** field: `open`, `in-progress`, or `closed`.

When closing an issue, set `**Status:** closed` and add a `**Closed:** YYYY-MM-DD` date.
**Closed issues are pruned from this file immediately upon closing** – their full text
lives in git history and can be retrieved with the commands below.

---

## Finding past issues in git

Closed issue blocks were removed from this file to keep the agent context lean.
The full text of every issue is preserved in git history.

```bash
# Show every commit that touched ISSUES.md (one line each)
git log --oneline -- ISSUES.md

# Search commit messages for an issue number or keyword
git log --oneline --all --grep="#24" -- ISSUES.md
git log --oneline --all --grep="keyboard" -- ISSUES.md

# Show the full diff for a specific commit (replace <hash> with the commit hash)
git show <hash> -- ISSUES.md

# Show the state of ISSUES.md as it was at a given commit
git show <hash>:ISSUES.md | less

# Grep across ALL historical versions of ISSUES.md for a keyword
git log -p -- ISSUES.md | grep -A 20 "ArrowLeft must update"

# Find the commit that removed a specific issue block
git log -p -- ISSUES.md | grep -B 5 "^-## #34"
```

---

## #49 – CSV preview shows "not yet implemented" stub

**Type:** feature
**Status:** in-progress

CSV files currently reach the server CSV provider, which returns a placeholder instead of useful row and value data. The shared browser UI also has no CSV virtual filesystem adapter, so local and server previews cannot expose CSV rows through the hierarchical navigation used by JSON and JSONL.

---

## #43 – Mobile preview fills 100 % width; rightmost column peek needed as scroll hint

**Type:** UX
**Status:** open

After #42, `#preview` is given `min-width: 90vw` on narrow viewports, but in practice it expands to fill the full available width, leaving no visible edge of the directory column to signal that the user can scroll left. The peek – a few pixels of the rightmost column visible on the right – is the essential affordance that makes the swipe gesture discoverable.

**Planned fix / implementation sketch:**

- Change the mobile media-query rule in `styles.py` from `min-width: 90vw` to a fixed `width: 90vw` (with `flex-shrink: 0` and `max-width: 90vw`) so the preview cannot grow past 90 % of the viewport regardless of content width.
- Ensure `#finder` retains `overflow-x: auto` so the remaining 10 % column peek is reachable by scrolling.
- Update the corresponding tests in `tests/test_rendering.py` that assert the mobile CSS values.

---

## #44 – ripgrep-based full-text search bar in `<nav>`

**Type:** feature
**Status:** open

There is no way to search file contents from the UI; users must know where a file lives to navigate to it. A search bar in the `<nav>` breadcrumb area should run `rg` against the ROOT directory and display matches as a results column, letting the user click a hit to open its preview.

**Planned fix / implementation sketch:**

- Add an `<input id="search-bar">` element to the breadcrumb in `columns.py` (`make_breadcrumb`), positioned after the existing buttons.
- Add a `/search?q=<query>` route in `app.py` that shells out to `rg --json -l <query> <ROOT>` (list-only mode), parses the JSON output, and returns an HTMX-swappable column `<div>` containing one `<li>` per matching file path (relative to ROOT), reusing the existing column CSS.
- Clicking a result `<li>` should trigger the normal `/click` flow so the file is previewed and the breadcrumb updates.
- Wire the `<input>` with `hx-get="/search"` `hx-trigger="input changed delay:300ms"` `hx-target="#search-results"` and inject an empty `<div id="search-results">` into the page.
- Add CSS for the search bar in `styles.py` (fits flush with the existing nav buttons).
- Guard against `rg` being absent (fall back to `pathlib` `rglob` + `Path.read_text` substring match with a 256 KB cap per file).
- Tests in `tests/test_app.py`: assert the `/search` route returns matching filenames; assert it returns an empty column for a query with no matches; assert it is safe (no path escape via query string).

---

## #45 – Mobile: column bottom clipped + directory nav scrolls to preview

**Type:** bug
**Status:** closed
**Closed:** 2026-03-12

Two related mobile UX regressions on narrow viewports:

1. **Column bottom clipped** – `body` and `#app-shell` use `height: 100vh`. Mobile
   browsers calculate `100vh` against the _large_ viewport (address bar hidden), so
   when the address bar is visible the bottom of each column is hidden behind it and
   cannot be scrolled to. Fix: add `height: 100dvh` (dynamic viewport height) after
   the `100vh` fallback in both rules.

2. **Directory nav scrolls to preview** – `htmx:afterSettle` unconditionally executes
   `finder.scrollLeft = finder.scrollWidth`, which on mobile snaps the scroll-snap
   container to the `#preview` pane after every HTMX settle – including after entering
   a directory. Only opening a _file_ should scroll the view right to show the
   preview; navigating into a _directory_ should keep the new directory column in view.
   Same bug exists in `_deepNavigate`.

**Planned fix:**

- Add `height: 100dvh` to `body` and `#app-shell` CSS rules (after the `100vh` fallback).
- Guard the `finder.scrollLeft = finder.scrollWidth` line in `htmx:afterSettle` with
  `e.detail.target && e.detail.target.id === 'preview'`.
- Guard the same line in `_deepNavigate` by checking that the preview element has child
  nodes before scrolling.

---

## #46 – Automatic dark mode following OS colour-scheme preference

**Type:** feature
**Status:** in-progress

The UI is hardcoded to a light theme (`background: #f0f0f0`, white columns, dark text).
Users whose OS is set to dark mode see a jarring white page. Filemill should
automatically switch to a dark palette when the browser reports
`prefers-color-scheme: dark`.

**Planned fix / implementation sketch:**

- Define a dark colour palette as CSS custom properties on `:root` and override them
  inside `@media (prefers-color-scheme: dark)` in `styles.py`. Key surfaces to
  retheme: `body` background, `#breadcrumb`, `.column` background/border,
  `#preview` background, `.column li a` text/hover/selected colours, `.preview-md`
  code/blockquote/table backgrounds, Pygments theme (switch to a dark-friendly
  style such as `monokai` or `github-dark`).
- Update `manifest.json` to set `"background_color"` and `"theme_color"` for
  the dark variant (or use `"theme_color"` that works for both).
- Add tests asserting that the `@media (prefers-color-scheme: dark)` block is
  present in the emitted CSS and that it overrides the key custom properties.

---

## #47 – Column width & scrolling UX: jumps, long-name stretch, no left-scroll

**Type:** bug / UX
**Status:** open

Three related column-width / scrolling problems on desktop:

1. **Width jumps** – `recalcColumnWidth()` recalculates `--col-width` after every
   HTMX settle, measuring the longest anchor across _all_ columns. When a new
   column with a longer (or shorter) name appears, every column resizes at once,
   causing a jarring "jump".

2. **Single long filename stretches column** – a single entry with a very long name
   (e.g. a 120-character filename) inflates the computed width for every column,
   wasting horizontal space even though only one entry is that wide.

3. **All columns stay visible** – `#finder` is `overflow-x: auto` but
   `recalcColumnWidth` constrains each column so that all columns + preview fit in
   the viewport. The macOS Finder lets old columns scroll off the left edge of the
   window; filemill should do the same.

**Planned fix / implementation sketch:**

- **Per-column width** – measure each column independently and set an inline
  `style="width: Xpx"` (or a scoped CSS variable) instead of a single global
  `--col-width`. This confines a long filename's width impact to its own column.
- **Max column width cap** – clamp each column to e.g. `min(measuredWidth, 360px)`
  so one long name never makes a column absurdly wide. Filenames beyond the cap
  are truncated with `text-overflow: ellipsis` (already applied in CSS).
- **Allow columns to scroll off-screen** – remove the
  `available = window.innerWidth - PREVIEW_MIN` / `maxWidth = available / colCount`
  logic that tries to fit everything on screen. Let columns keep their natural
  (capped) width and rely on `#finder { overflow-x: auto }` to scroll. Auto-scroll
  the newest column into view after each navigation (`scrollIntoView({ inline: 'end' })`).
- **Smooth transitions (optional)** – add `transition: width 0.15s ease` on
  `.column` to soften any remaining width changes.
- Update `recalcColumnWidth` tests if any exist; add new tests asserting per-column
  sizing and the max-width cap.

---

## #48 – Truncate filenames preserving the file extension

**Type:** UX
**Status:** open

Long filenames are currently truncated with a plain CSS `text-overflow: ellipsis`,
producing e.g. `very long filena...`. The file extension – often the most important
clue about a file's type – is hidden. Filenames should be truncated as
`very long fi...pdf` (or `very long fi….pdf`), keeping the last few characters
(typically the dot + extension) always visible.

**Planned fix / implementation sketch:**

- In `columns.py`, split each filename into a stem and a suffix
  (`Path.stem` / `Path.suffix`). Emit the anchor content as two inline elements:
  `<span class="fn-stem">{stem}</span><span class="fn-ext">{suffix}</span>`.
- CSS: `.fn-stem` gets `overflow: hidden; text-overflow: ellipsis; min-width: 0;
flex-shrink: 1`. `.fn-ext` gets `flex-shrink: 0; white-space: nowrap`.
  Wrap both in a flex container (`display: inline-flex; max-width: 100%`) inside the
  existing `<a>`.
- Files with no extension (or names like `.gitignore`) render as a single span
  with the current ellipsis behaviour.
- Update `test_columns.py` to assert the two-span structure and that the extension
  span is present for representative filenames.

---

## #49 – CSV preview shows "not yet implemented" stub

**Type:** bug
**Status:** open

`csv_provider.py` returns a static `<em>CSV VFS not yet implemented.</em>` message
for every `.csv` file. Users see this instead of the file's actual content.

**Planned fix / implementation sketch:**

- In `CSVProvider.render_preview`, read the CSV with `csv.reader` (or
  `csv.DictReader` for header detection).
- For `fmt="spreadsheet"` (default), render an HTML `<table>` with the same
  `.db-table` / `.preview-db-spreadsheet` CSS already used by the SQLite provider,
  including sticky headers and pagination (`page` / `limit` params).
- For `fmt="raw"`, fall back to the existing plain-text preview path (read file
  bytes, render as `<pre class="preview-raw">`).
- Implement `list_entries` to return one `VFSEntry` per row (like SQLite rows)
  for the column-navigation mode.
- Add tests in a new `tests/test_providers_csv.py`: round-trip a small CSV through
  `render_preview` and assert table headers, row count, pagination, and the raw
  fallback.

---

## #50 – ArrowRight after ArrowLeft loses previously focused item

**Type:** bug
**Status:** open

Steps to reproduce:

1. Navigate into a directory with the keyboard (ArrowRight).
2. In the child column, move to an item other than the first (ArrowDown a few times).
3. Press ArrowLeft to go back to the parent column.
4. Press ArrowRight to re-enter the same directory.

**Expected:** the previously highlighted item in the child column is re-selected.
**Actual:** the first item in the column is selected.

**Root cause:** the ArrowLeft handler in `COLUMN_JS` removes the focused column and
all columns to its right from the DOM (`el.remove()`). When ArrowRight triggers
`triggerNav` → HTMX fetch → `htmx:afterSettle`, the column is rebuilt from scratch
with no memory of the prior selection. The `afterSettle` handler then runs
`selectLi(items[0])` because `getSelectedLi(newCol)` is null.

**Planned fix / implementation sketch:**

- Maintain a `Map<colIndex, vpathOrName>` (or a plain object keyed by the parent
  path) that records which entry was last selected in each column.
- On every `selectLi` call (or in the click handler), write the selected entry's
  identifier into this map.
- When `htmx:afterSettle` detects a new column (`isNewCol`), look up the map for
  that column's parent path. If a match is found, highlight that item instead of
  `items[0]`.
- Clear map entries for columns that are pruned (ArrowLeft / prune script).
  Only clear entries for columns _deeper_ than the one being returned to, so the
  immediate child's memory is preserved.

---

## #51 – PWA: start the Filemill HTTP service alongside the installed app

**Type:** feature / research
**Status:** open

When filemill is installed as a PWA (Add to Home Screen), opening it navigates to
`http://localhost:8334/f/` – but nothing ensures the server is actually running.
If the user hasn't manually started `filemill` in a terminal, the PWA shows a
connection-refused error.

This is a fundamental limitation: a PWA is a browser sandbox and cannot spawn local
processes. Possible approaches (each with trade-offs):

1. **System service (systemd / launchd)** – ship a `filemill.service` unit (Linux)
   or a `launchd` plist (macOS) that auto-starts the server on login. The PWA then
   always finds a running server. Downside: requires a one-time install step outside
   the browser (`systemctl --user enable filemill`).

2. **Desktop `.desktop` / `.app` launcher** – provide a launcher that starts the
   server _and_ opens the browser/PWA. On Linux this is a `.desktop` file with
   `Exec=filemill --open`; on macOS an Automator app or shell wrapper. Not a
   true "PWA starts the server" solution, but gives a single-click experience.

3. **Electron / Tauri wrapper** – bundle the Python server inside a desktop app
   shell that manages the process lifecycle. Full native experience but a much
   heavier packaging story.

4. **Offline-capable service worker** – enhance `sw.js` to cache the UI shell and
   show a friendly "server not running – start it with `filemill`" message instead
   of a raw browser error. Doesn't solve the problem but improves the failure mode.

**Next step:** decide which approach (or combination) to pursue; file a follow-up
issue for the chosen implementation.

---

## #52 – Markdown raw source view toggle

**Type:** feature
**Status:** open

Markdown files are always shown rendered. Add a **Rendered / Raw** toggle button bar —
analogous to the JSON formatted/raw toggle — so the user can inspect the raw `.md` source
without leaving filemill.

**Planned fix / implementation sketch:**

- Add `providers/markdown_provider.py` with a `MarkdownProvider` class implementing the
  `VFSProvider` protocol. `default_fmt` returns `"rendered"`. `list_entries` returns `[]`
  (markdown is a leaf node). `render_preview(fmt="raw")` returns
  `<pre class="preview-raw">` with HTML-escaped source; `fmt="rendered"` delegates to the
  existing `render_markdown()` pipeline in `rendering.py`.
- Register `MarkdownProvider` in the VFS `REGISTRY` in `vfs.py` (alongside `JSONProvider`
  and `CSVProvider`).
- The format-toggle bar (`show_fmt_bar=True` in `list_vfs_column()`) and localStorage
  persistence (`vfmt_type_.md`) are handled automatically by existing machinery in
  `columns.py` and `styles.py` — no new JS or CSS needed.
- Button labels: `📄 Rendered` (`data-fmt="rendered"`) and `📝 Raw` (`data-fmt="raw"`).
- Tests: `tests/test_providers.py` — assert rendered output contains `<p>` tags, assert
  raw output is a `<pre>` containing the literal source text.

**Tracked in pykoclaw backlog:** `filemill-markdown-raw-toggle`

---

## #53 – VTT subtitle file preview (Transcript / Raw toggle)

**Type:** feature
**Status:** open

`.vtt` (WebVTT) subtitle files fall through to the plain `<pre>` text fallback. Add a
`VTTProvider` with a clean **Transcript** view (timestamps stripped, cues joined into
readable paragraphs) as the default, and a **Raw** toggle for the source — same pattern
as #52 (Markdown) and the JSON formatted/raw toggle.

**Planned fix / implementation sketch:**

- Add `providers/vtt_provider.py` with `VTTProvider`. `default_fmt` returns `"transcript"`.
  `list_entries` returns `[]` (leaf node). `render_preview(fmt="transcript")` parses cue
  blocks via regex (split on blank lines, skip `WEBVTT`/`NOTE`/`STYLE` headers and
  timestamp lines, strip inline `<c>` / `<00:…>` tags), emits `<div class="preview-transcript">`
  with `<p>` per cue (or per merged short-cue group). If `<v Speaker>` voice spans are
  detected, emit `<strong>Speaker:</strong>` labels. `render_preview(fmt="raw")` returns
  `<pre class="preview-raw">` with HTML-escaped source.
- Register `VTTProvider` in the VFS `REGISTRY` in `vfs.py`.
- Add `.preview-transcript` CSS rule to `styles.py` (padding, line-height, `overflow-y: auto`).
- Format-toggle bar: `📜 Transcript` / `📝 Raw` — existing `.fmt-bar` machinery and
  `vfmt_type_.vtt` localStorage key handle persistence automatically.
- Tests in `tests/test_providers.py`: transcript strips timestamps and inline tags, raw
  passthrough, speaker label extraction, empty-cue and malformed-header edge cases.

**Tracked in pykoclaw backlog:** `filemill-vtt-preview`

## #54 – Home-directory tilde links don't work in rendered Markdown

**Type:** bug
**Status:** open

Links written as `[text](~/some/path.md)` render as dead links in Filemill — clicking
them gives a 404 or navigates nowhere, even though the file exists.

**Root cause / technical sketch:**

Filemill is launched as `filemill /home/agent/menu`. The serve root maps
`/f/menu/` → `/home/agent/menu/`, and `/home/agent/menu/agent` is a symlink back to
`/home/agent/`. Tilde (`~`) therefore resolves to `/home/agent/`, which corresponds
to the URL prefix `/f/menu/agent/`.

The Markdown renderer must expand `~/foo/bar.md` → `/f/menu/agent/foo/bar.md` before
writing the `href`. The expansion rule is:

```
~/path  →  /f/<serve-root-name>/agent/path
```

where `<serve-root-name>` is derived from the `--root` argument and `agent` is the
symlink entry that resolves to `$HOME`.

**Steps to reproduce:** Open any Markdown note that contains a `[label](~/some/file.md)` link and click it.

---

## #55 – PWA worker intercepts shared-UI API requests

**Type:** bug
**Status:** closed

The service worker registered by the HTMX UI controlled the shared UI under
`/n/`. It tried to cache `POST /api/render` and could cache responses from
`GET /api/*`. This could break local-file previews or show stale file data.

The worker now bypasses non-GET requests and `/api/*`. The shared UI also
registers the worker, so the PWA setup does not depend on a prior visit to
`/f/`.

---

## Open issues

_See each issue's status above._
