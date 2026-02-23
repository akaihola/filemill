# fndr — Project Agent Guide

## What this project is

A single-file PWA that faithfully reproduces **macOS Finder in Column View mode**.
No external dependencies — everything (HTML, CSS, JS, PWA manifest, service worker)
must be inlineable into one `dist/index.html`.

Reference screenshot: `/tmp/pi-clipboard-4627ac20-3cc7-4de8-9aa4-e77f1e276e89.png`
(macOS Finder, Column View, with `ColumnView.tiff` selected inside
`OWC / Images / Finder Views Column Cover`).

---

## Agent memory convention

Whenever the user says "remember X" or "always do Y", or whenever you detect
a project-specific rule worth preserving, **immediately update this file** with
the new rule or fact before doing anything else. Same applies to any correction
the user makes to your behaviour — capture it here so it survives a context reset.

---

## How to orient yourself after a crash

1. **Read `TASKS.md`** — canonical list of open, in-progress, and done work.
2. **Take a screenshot** (see below) and compare against the reference image.
3. Check `src/` for the current dev-mode split files; `dist/index.html` for the
   last built single-file output; `index.html` for the dev entry point.

---

## File layout

```
fndr/
├── AGENTS.md          ← this file
├── TASKS.md           ← open task list (read first every session)
├── index.html         ← dev entry point (links to src/ files)
├── build.py           ← Python bundler → dist/index.html
├── build.sh           ← thin shell wrapper: python3 build.py
├── dist/
│   └── index.html     ← production single-file output (run build.py to refresh)
└── src/
    ├── styles.css
    ├── mock-data.js   ← MOCK_FS, SIDEBAR_ITEMS, SIDEBAR_TAGS
    ├── icons.js       ← all SVG icon functions (small + big + sidebar)
    ├── fsa.js         ← File System Access API (makeFSANode, ensureLoaded, …)
    ├── navigation.js  ← state vars, initToMockPath, navigateTo, history
    ├── render.js      ← renderSidebar/Columns/Preview/PathBar/StatusBar, applyColumnWidths
    ├── events.js      ← all addEventListener calls
    └── main.js        ← PWA manifest+SW setup, initial navigation, focus
```

> The split into `src/` files and `build.py` is **fully implemented**.
> `index.html` is the dev entry point; `dist/index.html` is the built bundle.

---

## Hot-reload during development

Chromium at port 9222 hosts the live page. **Never reload the page** while FSA
directories have been authorised — that discards all `FileSystemHandle` grants.

Instead run the hot-reloader in a separate tmux pane:

```bash
uv run --with "playwright==1.57.0" python3 hotreload.py
```

It watches `src/` every 250 ms. On change:

| File type | Mechanism | State impact |
|-----------|-----------|-------------|
| `.js` | `Debugger.setScriptSource` CDP command | **Zero** — function bodies updated in-place; all `let` variables, FSA handles untouched |
| `.css` | Injects `<style id="fndr-hot-css">` | Visual only — no JS state |

**Limitation**: `setScriptSource` can update existing function bodies but cannot add
brand-new top-level `let` variables to an already-running script. For structural
changes (new state vars) a full reload is required, but FSA handles will survive
because `restoreFSAHandlesFromIDB()` re-grants them automatically on reload (as long
as `queryPermission()` returns `'granted'` — typically true within the same
browser session).

**Quick JS eval without Playwright**: `uvx rodney js '<expr>'` for one-liners;
connect to port 9222 implicitly.

---

## FSA handle persistence (IndexedDB)

`FileSystemHandle` objects are structured-cloneable and survive storage in
IndexedDB. `fndr-fsa` database, `handles` object-store, keyed by `label`.

- **Save**: `saveFSAHandlesToIDB()` — called automatically after each
  `openFolderPicker()` success.
- **Restore**: `restoreFSAHandlesFromIDB()` — called from `main.js` at startup;
  uses `handle.queryPermission({ mode: 'read' })` (no user gesture needed);
  only `'granted'` handles are added to the sidebar silently. `'prompt'`/`'denied'`
  handles are skipped (user must re-open with the toolbar button).
- Each `unshift` increments `activeSidebarIdx` by 1 to compensate for the index
  shift (otherwise the sidebar's selected item would point to the wrong entry).

---

## Taking screenshots for visual testing

Use Python Playwright pinned to the version matching the NixOS-installed browsers.
**Never run `playwright install`.**

```bash
uv run --with "playwright==1.57.0" python3 - << 'EOF'
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        await page.goto('file:///home/akaihola/prg/fndr/index.html')
        await page.wait_for_timeout(1200)
        await page.screenshot(path='/tmp/fndr-test.png')
        await browser.close()
        print('done')

asyncio.run(main())
EOF
```

Pin rationale:

- `$PLAYWRIGHT_BROWSERS_PATH` = NixOS-installed Chromium **rev 1200**
- `playwright==1.57.0` targets exactly rev 1200
- `UV_CONSTRAINT` also specifies `playwright==1.57.0` but that var is **not**
  applied automatically to `uv run --with` — always write the version explicitly

---

## Key design decisions


pi install npm:pi-extmgr
| Decision                                    | Rationale                                                                       |
| ------------------------------------------- | ------------------------------------------------------------------------------- |
| Single output file (`dist/index.html`)      | PWA must be fully self-contained                                                |
| `position: fixed; inset: 0` on `#finder`    | Guaranteed viewport fill regardless of body sizing                              |
| `#main { flex: 1; min-height: 0 }`          | Prevents flex children from overflowing in column layouts                       |
| Columns rooted at sidebar selection         | Matches real Finder: sidebar item = mount point                                 |
| Entire selection chain shown in blue        | Real macOS Finder behaviour: all ancestors of deepest selection are highlighted |
| `--col-width` CSS variable                  | Dynamic width computed after render via `canvas.measureText()`                  |
| Global resize (all columns move together)   | Matches real macOS Finder column-view resize behaviour                          |
| Lazy FSA directory loading (`ensureLoaded`) | Avoid reading the full tree up front; only expand on demand                     |
| History stores direct node references       | Avoids needing to serialise/re-find FSA `FileSystemHandle` objects              |
| `node._lastSelected`                        | Each folder node remembers its last-selected child; right-arrow restores it — including when returning from sidebar via ArrowRight |
| `sidebarFocused` flag                       | Left-arrow at leftmost column retreats to sidebar; ↑/↓ navigate items there    |
| Type-ahead: prefix → substring → fuzzy      | Smart in-column search on printable keys; `<mark>` highlights in focused column |
| `skipHistory` in `navigateTo`               | Type-ahead navigates without polluting history; commits on clear                |
| Window title = `columns.at(-1)?.node.name` | Shows deepest open folder, not selected file — matches real macOS Finder        |
| Path bar for builtins → label only          | `renderPathBar()` shows just `si.label` (e.g. "AirDrop") when `sidebarBuiltin` |
| Home/End in column                          | Jump to first/last item in focused column (events.js)                           |
| History capped at 100                       | `pushHistory()` shifts oldest entry when stack exceeds 100                      |
| FSA handles → IndexedDB (`fndr-fsa`)        | `saveFSAHandlesToIDB()` / `restoreFSAHandlesFromIDB()` in fsa.js; only 'granted' handles restored silently (requestPermission needs a user gesture) |
| Hot-reload via `hotreload.py`               | Uses `Debugger.setScriptSource` CDP command; JS function bodies updated in-place, all page state (incl. FSA handles) preserved. CSS injected via `<style id="fndr-hot-css">`. Run with `uv run --with "playwright==1.57.0" python3 hotreload.py`. The `Runtime.evaluate` fallback only re-injects extracted function declarations (not top-level addEventListener calls) to avoid duplicate listener registration. |

---

## CSS / JS architecture notes

**Load order of src/ scripts** (dependency order):

1. `icons.js` — no deps
2. `mock-data.js` — uses `sidebarIcon` / `sidebarFolderIcon` from icons.js
3. `navigation.js` — state vars + helpers; defines `getFileType`, `formatFileSize`, `formatDate`
4. `fsa.js` — runtime deps on `render()` and `pushHistory()` (loaded later; fine because only called at runtime)
5. `render.js` — uses state from navigation.js, icons from icons.js, data from mock-data.js
6. `events.js` — wires up all DOM listeners
7. `main.js` — PWA setup, initial `initToMockPath(…)` call

**Global state** (all `let`, declared in `navigation.js`):

- `columns` — `[{ node, selectedName }]`, rooted at sidebar selection
- `selectedFile` — node or null; drives preview panel
- `sidebarRootNode` / `sidebarRootPath` — current sidebar anchor
- `historyStack` / `historyIndex` — back/forward (stores node refs directly)
- `searchQuery`, `activeSidebarIdx`, `globalColWidth`
- `focusedColIdx` — index of the column that has keyboard focus (-1 = none)
- `sidebarFocused` — true while keyboard focus is inside the Favorites sidebar
- `colSearch` / `colSearchTimer` — type-ahead query string + auto-clear timer

**Node shape:**

```js
// Mock node (static)
{ name, type, children?, size?, dims?, created?, modified?, lastOpened? }

// FSA node (lazy)
{ name, type, handle, children: null|[], _loading: bool, _metaLoaded: bool, size?, modified? }
// children === null  → not yet loaded (directory)
// children === []    → loaded, empty  OR file (no children property at all for files)
```

---

## Visual spec (quick reference)

- Font: `-apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif`, 13 px
- Titlebar: `linear-gradient(#d8d8d8, #c8c8c8)`, 52 px, traffic lights 12 px circles
- Toolbar: same gradient, 38 px
- Sidebar: 175 px wide, `rgba(236,236,236,0.9)`, section headers 11 px uppercase
- Sidebar selected: `rgba(9,103,210,0.14)` bg, `#0f62d1` text
- Column item height: 22 px; selected-active: `#1070cf` bg, white text
- Column separator: `1px solid #d0d0d0`
- Preview panel: 240 px wide, `#f5f5f5` bg
- Path bar: 24 px, `rgba(236,236,236,0.97)`, separator `▸`
- Status bar: 20 px, `#ececec`
