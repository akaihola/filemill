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

## #46 – Markdown raw source view toggle

**Type:** feature
**Status:** open

Markdown files are always shown rendered. Add a **Rendered / Raw** toggle button bar —
analogous to the JSON formatted/raw toggle — so the user can inspect the raw `.md` source
without leaving pykofinder.

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

**Tracked in pykoclaw backlog:** `pykofinder-markdown-raw-toggle`

---

## #47 – VTT subtitle file preview (Transcript / Raw toggle)

**Type:** feature
**Status:** open

`.vtt` (WebVTT) subtitle files fall through to the plain `<pre>` text fallback. Add a
`VTTProvider` with a clean **Transcript** view (timestamps stripped, cues joined into
readable paragraphs) as the default, and a **Raw** toggle for the source — same pattern
as #46 (Markdown) and the JSON formatted/raw toggle.

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

**Tracked in pykoclaw backlog:** `pykofinder-vtt-preview`

---

## Open issues

_Items above are all currently open._
