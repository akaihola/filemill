# fndr — Open Task List

Legend: `[ ]` open · `[~]` in-progress / partially done · `[x]` done

---

## 🗂 Project structure

- [x] **Split into src/ files** — HTML template, CSS, and JS split by area:
  - `src/styles.css`
  - `src/mock-data.js`
  - `src/icons.js`
  - `src/fsa.js` (File System Access API)
  - `src/navigation.js` (state + column logic)
  - `src/render.js` (all render functions)
  - `src/events.js` (event listeners)
  - `src/main.js` (PWA setup + init)
- [x] **`build.py`** — Python bundler that inlines all src/ files into `dist/index.html`
- [x] **`build.sh`** — thin shell wrapper around `build.py`
- [x] **`index.html` (dev)** — references `src/` files via `<link>` / `<script src=...>`

---

## 🐛 Bugs — user-reported

- [x] **Left arrow in leftmost column should move focus to Favorites sidebar** —
      sets `sidebarFocused = true` + `focusedColIdx = -1`; sidebar item gets
      `.kbd-focused` outline (2px solid #1070cf); ↑/↓ navigates sidebar items;
      → or Enter moves focus back into columns.
- [x] **Right arrow should restore last-highlighted item** — `node._lastSelected`
      is stored in `navigateTo`; ArrowRight looks it up and falls back to
      `nextItems[0]` only if the folder was never visited.
- [x] **Returning from Favorites (sidebar) to leftmost column with ArrowRight
      doesn't restore the previously highlighted item** — `ArrowRight` handler
      inside `sidebarFocused` block now reads `columns[0].node._lastSelected`
      and calls `navigateTo(0, saved)` if set, mirroring the existing
      inter-column `_lastSelected` logic. Verified via CDP live test.

- [x] **Type-ahead search in focused column** — printable chars trigger smart
      search (prefix → substring → fuzzy); matching chars highlighted with
      `<mark>` in all column items; any non-typing action (arrow, click, 1.5 s
      idle) clears the search and removes highlights. No history push during
      type-ahead; commit final position on clear.

- [x] **Right → into empty folder does nothing** — no-op when target column is
      empty; `focusedColIdx` does not advance; `navigateTo` only adds a child
      column when the folder actually has children
- [x] **Never show a rightmost empty (zero-item) column** — `navigateTo` now
      only pushes a new column when `child.children.length > 0`
- [x] **Left ← deselects deepest item and closes preview** — finds rightmost
      column with a `selectedName`, clears it, strips child columns,
      sets `selectedFile = null`, updates preview + path bar
- [x] **Left ← doesn't move focus to the column on the left** — after deselecting
      the rightmost selected item, `focusedColIdx` stays on the same column instead
      of moving to `rightmost - 1`; fixed by setting `focusedColIdx = Math.max(0, rightmost - 1)`

---

## 🐛 Bugs — self-observed (visual)

- [x] **Blank ~130 px gray strip at the bottom of the window** — `position: fixed;
      inset: 0` on `#finder` confirmed working in headless screenshots; window
      fills full viewport with no gray strip visible.
- [x] **Path bar separator renders as `»` not `▸`** — bumped to `11px` /
      `#888`; now clearly legible as `▸` in screenshots.
- [x] **`--col-width` CSS variable not wired up** — already wired:
      `.col { width: var(--col-width, 185px); }` confirmed in styles.css.
- [x] **Sidebar `activeSidebarIdx` hard-coded as `4`** — now derived in
      `main.js` via `SIDEBAR_ITEMS.findIndex(s => s.label === 'OWC')`.

---

## ✨ Features — user-requested

- [x] **Dynamic column width** — after each render, `applyColumnWidths()` in
      render.js computes `width = min(widestItemTextWidth + padding,
      floor(availableWidth / numColumns))` using `canvas.measureText()`. Applied
      via `--col-width` CSS variable. Drag-resize stores result in `globalColWidth`
      (navigation.js), overrides the computed value, and all columns resize
      together (matching real macOS Finder behaviour). Reset on sidebar change.
- [x] **File System Access API** — `showDirectoryPicker()`, lazy per-directory
      loading (`ensureLoaded`), file metadata on select (`loadFileMeta`).
      Tested end-to-end with `fsa-test.py` (11/11 passed, real ~/prg folder).
      Confirmed: real directory listing, file size+modified from `getFile()`,
      no Created row, sub-folder lazy load, cancel/abort handling, unsupported-
      browser alert. Manual visual checklist: `FSA-TEST-CHECKLIST.md`.

  Bugs fixed before test:
  - `events.js`: keyboard ↑/↓ to FSA sidebar item didn't update `columns`,
    `sidebarRootNode`, `sidebarRootPath` — showed stale mock data
  - `navigation.js`: child column pushed to `columns` AFTER `ensureLoaded()`,
    so the spinner `render()` fired against the wrong column; now pushed first
  - `fsa.js`: same issue for root — state now set before `ensureLoaded()` so
    the spinner renders into column 0 correctly
  - `events.js`: `if (!col) return` blocked ArrowLeft when `columns = []`
    (builtin empty-state); changed to `if (!col && e.key !== 'ArrowLeft') return`

  Live CDP test results (35 checks, 1 expected skip):
  ✅ Column 0: 59 items, no dot-files, folders before files, alphabetical
  ✅ File preview: name, kind, size (380 bytes), modified (5.5.2025), no Created row
  ✅ Status bar "1 of N selected", path bar, window title all update
  ✅ Sub-folder: fndr→10 items, fndr/src→8 items, path bar 3 levels deep
  ✅ Keyboard: ↓↑ move, → opens col, focus tracking, ← to sidebar
  ✅ Type-ahead: prefix match, <mark> highlight, multi-char refine, Escape clear
  ✅ Search: 59→1 for 'fndr', all match, clear restores 59
  ✅ History: Back/Forward round-trip through sub-folder
  ✅ Empty folder: no arrow, no new column opens
  ✅ Cancel picker (AbortError): UI unchanged
  ✅ Unsupported browser alert
  ✅ Keyboard sidebar FSA nav: ←→sidebar→↓iCloud→↑prg loads columns
  ✅ Column resize: 223→304px, resets to auto on sidebar click
  ✅ Duplicate prevention: sidebar stays 17 items after re-open
  ✅  ArrowLeft from builtin empty-state: verified via rodney live test after hot-reload

---

## 🐛 Bugs — found during polish pass

- [x] **ArrowLeft from builtin empty-state (columns=[]) crashes silently** —
      `getChildrenFiltered(col.node)` threw TypeError when `col` is `undefined`;
      guarded with `col ? ... : []` so ArrowLeft correctly reaches `sidebarFocused=true`.
      Verified via rodney live test.

- [x] **Path bar shows stale path when switching to builtin sidebar item** —
      `renderPathBar()` now detects `sidebarBuiltin` and replaces the path with
      just the active sidebar item's label (e.g. "AirDrop").

- [x] **Window title (`#window-title` span) was hardcoded; never updated** —
      `render()` now sets it dynamically. Rule: deepest open folder name
      (`columns.at(-1)?.node.name`) — matches real macOS Finder behaviour where
      the title shows the folder whose *contents* are displayed, not the selected
      file's own name. Falls back to sidebar item label or "Finder".

---

## 🛠 Developer tooling

- [x] **`hotreload.py`** — watches `src/` every 250 ms; patches live Chromium
      at port 9222 without page reload (preserves FSA grants):
      - JS: `Debugger.setScriptSource` (updates function bodies in-place)
        followed by `Runtime.evaluate` with `let`/`const`/`var` top-level
        declarations stripped (so new functions land in global scope).
      - CSS: injects `<style id="fndr-hot-css">` replacing the original sheet.
      - Run: `uv run --with "playwright==1.57.0" python3 hotreload.py`

- [x] **FSA IndexedDB persistence** — `FileSystemHandle` objects stored in
      `fndr-fsa` IDB under `handles` key; `saveFSAHandlesToIDB()` called after
      each `openFolderPicker()` success; `restoreFSAHandlesFromIDB()` called at
      startup in `main.js` — silently re-adds handles with `'granted'`
      permission (no user gesture needed for `queryPermission`).
      Each `unshift` also increments `activeSidebarIdx` to keep it pointing at
      the same (now-shifted) sidebar item.

---

## ✨ Features — polish / self-identified (session 3)

- [x] **Home / End keys** — jump to first / last item in the focused column;
      handled alongside ArrowUp/Down in `events.js`.
- [x] **History cap** — `pushHistory()` now trims `historyStack` to 100 entries
      max; older entries are shifted out to avoid unbounded memory growth.

---

## ✨ Features — polish / self-identified

- [x] **Scroll selected item into view within its column** — `scrollSelectedIntoView()`
      in render.js calls `el.scrollIntoView({ block: 'nearest' })` on each
      `.col-item.selected-active` element via `requestAnimationFrame` after render.
- [x] **Focus ring on focused column** — `.col.focused` gets
      `box-shadow: inset 0 0 0 2px rgba(16,112,207,0.35)` (styles.css).
- [x] **Window title updates** — `document.title` is set in `render()` to
      `"<selectedName> — Finder"` or `"Finder"` when nothing is selected.
- [x] **Empty-state messaging** — builtin sidebar items (AirDrop, iCloud Drive,
      All My Files, Dropbox) set `sidebarBuiltin = true`; `renderColumns()` clears
      columns and shows a centred `"<Label> is not available in this view."` div
      absolutely positioned inside `#columns-container`. Regular mock/FSA items
      set `sidebarBuiltin = false`. State persisted across history.
- [x] **Keyboard focus after sidebar click** — sidebar click handler calls
      `document.getElementById('columns-container').focus()` after `render()`.

---

## ✅ Already done

- [x] Traffic lights + macOS window chrome
- [x] Toolbar (Back/Forward, view-mode buttons, action buttons, search, Open… button)
- [x] Sidebar with FAVORITES and TAGS sections, coloured icons, selected highlight
- [x] Column view — multiple scrollable columns, folder ▶ arrows, selection chain
      all blue (entire path highlighted)
- [x] Preview panel — big icon, filename, file-type label, metadata rows, Add Tags…
- [x] Path bar with ▸ separators, clickable breadcrumbs
- [x] Status bar — "N of M selected / N items / 709.59 GB available"
- [x] Column resize drag handle — global (all columns resize together via `--col-width`)
- [x] Back / Forward history (in-memory, direct node references)
- [x] Search filter — live, case-insensitive substring
- [x] View-mode button toggle (visual only)
- [x] PWA manifest + inline service worker
- [x] Column view roots at sidebar selection (not at FS root)
- [x] Columns start from sidebar node; ancestry shown only in path bar
- [x] `position: fixed; inset: 0` applied to `#finder` — confirmed working
- [x] File System Access API code written (untested in headless env)
- [x] Split into `src/` files + `build.py` bundler; `dist/index.html` pixel-identical to original
