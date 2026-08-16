# filemill — Project Agent Guide

## What this project is

A file manager that browses a **real local folder** in **Miller columns**, and
ships as one self-contained `index.html`. No network, no server, no example
content: the app opens on a folder picker and everything it shows comes from the
directory the user grants, read through the File System Access API.

The UI comes from the "Trail" Miller-columns design study
(`~/.kandev/tasks/let-s-explore-nicer_5oguwwan/pykofinder/design/miller-columns.html`):
column headers with counts, three distinct selection states, a drawn trail
between selected rows, and horizontal scroll as a 0–100 % *condensing dial* that
folds columns into spines from the left.

---

## Agent memory convention

Whenever the user says "remember X" or "always do Y", or whenever you detect
a project-specific rule worth preserving, **immediately update this file** with
the new rule or fact before doing anything else. Same applies to any correction
the user makes to your behaviour — capture it here so it survives a context reset.

---

## File layout

```
filemill/
├── AGENTS.md               ← this file
├── TASKS.md                ← open task list
├── FSA-TEST-CHECKLIST.md   ← what the automated tests cannot check
├── index.html              ← GENERATED bundle (do not hand-edit)
├── build-index.py          ← src/index.html + assets → index.html
├── hotreload.py            ← optional CDP live-patcher for dev mode
├── test-ui.py              ← headless suite, fake handle (28 checks)
├── test-e2e.py             ← headed suite, real folder + real picker
├── src/                    ← THE SOURCE
│   ├── index.html          ← dev entry point: <link>/<script src> references
│   ├── styles.css          ← every design token + rule
│   ├── fs.js               ← FSA layer: mkNode, ensureLoaded, loadMeta, fmt*
│   ├── icons.js            ← Seti lookup, folder glyph, esc()
│   ├── state.js            ← globals, visibleKids, measure, previewNode
│   ├── render.js           ← buildCol, columnFor, render, preview
│   ├── layout.js           ← the fold dial: stripSpan, layout, applyScroll
│   ├── trail.js            ← the SVG elbows between columns
│   ├── nav.js              ← choose(), crumbs, all keyboard handling
│   ├── settings.js         ← ⚙ popover toggles
│   ├── storage.js          ← IndexedDB: remembered folders
│   └── main.js             ← mount, picker, welcome screen, startup
└── vendor/
    ├── seti-map.js         ← extension → [codepoint, colour] (MIT)
    ├── seti.woff           ← Seti UI icon font (MIT)
    └── SETI-LICENSE.md
```

**Edit `src/`, never `index.html`.** Two ways to run what you edited:

```bash
python3 -m http.server 8000 -d .     # then …
#   http://localhost:8000/src/index.html    ← dev, no build step, real files
./build-index.py                     #   → index.html (~119 KB, self-contained)
#   http://localhost:8000/index.html        ← the bundle
```

`build-index.py` inlines each `<link rel=stylesheet>` and `<script src>` the
browser would have fetched, and swaps the `@font-face` URL for a base64 data
URI — the same trick the old `build.py` used, extended to cover the font.

---

## Serve it over localhost — `file://` cannot work

Chrome refuses `showDirectoryPicker()` on an opaque origin, which is what a
`file://` page has. Double-clicking `index.html` therefore shows an explanatory
welcome screen instead of a folder, by design (`showBlocked("file")` in
`main.js`, triggered both up front from `location.protocol` and from the
`SecurityError`). This is the single most common "it's broken" report.

---

## Remembered folders (IndexedDB)

`FileSystemHandle` is structured-cloneable, so `storage.js` keeps the last 8
picked roots in the `filemill` database, `kv` store, key `recent`.

- `rememberRoot()` after every successful pick; `isSameEntry()` dedupes.
- `recallRoots()` at startup. `queryPermission()` needs no user gesture, so a
  folder still `'granted'` **re-mounts with no dialog at all**.
- Otherwise the roots are listed under "Recently opened" on the welcome screen;
  clicking one calls `requestPermission()` from that gesture. Chrome usually
  downgrades grants to `'prompt'` when the browser restarts, so expect one
  in-page permission bar per session — but never the OS picker again.

---

## Testing

```bash
uv run --with "playwright==1.61.0" python3 test-ui.py          # bundle
uv run --with "playwright==1.61.0" python3 test-ui.py --dev    # modular sources
uv run --with "playwright==1.61.0" python3 test-e2e.py         # real folder
```

**Never run `playwright install`.** Pin the version matching the
NixOS-installed browsers — currently rev 1228 → `playwright==1.61.0`, which is
also what `$UV_CONSTRAINT` says.

`test-ui.py` fakes the handle API, which is all the app ever touches:

```js
const D = (name, kids) => ({kind:'directory', name,
  entries: async function*(){ for (const k of kids) yield [k.name, k]; }});
const F = (name, text) => ({kind:'file', name,
  getFile: async () => new File([text], name, {lastModified: Date.now()})});
mount(D('workspace', [D('src', [F('app.py', 'print(1)')]), F('README.md', '# hi')]));
```

A `file://` page is fine for it — `mount(fake)` bypasses the picker. Measure
render cost **in-page** (`performance.now()` around `render()`), never by timing
Playwright keystrokes; the round-trip dominates. Budget: re-render ≤ 20 ms and
keystroke ≤ 25 ms at 3 000 entries (the suite asserts this).

`hotreload.py` patches `src/*.js` into a live page over CDP without reloading,
for when a permission re-grant would interrupt you. Mostly unnecessary now that
folders are restored from IndexedDB — reloading is cheap.

---

## Key design decisions

| Decision | Rationale |
| -------- | --------- |
| Modular `src/`, generated `index.html` | The deliverable must be one portable file; a 1 500-line blob with 50 KB of base64 in it is not maintainable. `src/index.html` runs unbuilt, so the dev loop has no build step |
| Focus follows the *selection*, not the newest column | ↑/↓ must keep walking the current column even when the rows are folders. Opening a folder shows its column but does not move focus; → moves in, ← moves out |
| `node.lastSel` per directory | → returns to the row you were on last time you were in that column, instead of always the first |
| Folder picker as a full-screen welcome state | `showDirectoryPicker()` needs a user gesture and there is nothing to show before one exists |
| `kids === null` means "not read yet" | Distinguishes an unread directory (spinner) from an empty one ("Empty") |
| `node.loading` promise, awaited by concurrent callers | Fast arrow-key navigation can hit the same directory twice before the first read finishes |
| Metadata fetched only on preview | `getFile()` is a syscall per file — per row it would stall large directories |
| `pvToken` guards preview fills | A slow read for a file you have navigated away from must not overwrite the current preview |
| Horizontal scroll = fold dial, not translation | `#stage` is sticky so nothing moves; `scrollLeft` is read as 0–100 %. Keeps the preview readable with no manual splitter |
| Column DOM cached per `(node, kids)` in `colCache` | Rebuilding a 3 000-entry column per keystroke cost ~500 ms. Re-renders now only re-apply depth/selection/cursor classes |
| Children reconciled, never `replaceChildren`d | Re-inserting an element detaches it and discards the style + layout of every row under it — that alone was the 500 ms |
| `set()` / `setVar()` write guards | Re-writing the width or a custom property a column already has still relays out all of its rows |
| `content-visibility: auto` on `.row` | Rows have a fixed height, so off-screen ones are skipped: forced layouts (`scrollIntoView`) stop being O(entries) |
| Click handler on `.col`, not just rows | A folded column hides its rows, so "click a spine to unfold" must be handled by the column (the design study advertised this but never wired it) |
| Read-only (`mode: "read"`) | Nothing in the app writes, so never ask for write permission |

---

## Visual spec

All of it is CSS custom properties at the top of `src/styles.css` — change the
tokens, not the rules. `data-theme="light|dark"` and
`data-density="compact|comfortable"` on `<html>` switch whole palettes and
metrics; both come from the ⚙ popover.

- Accent `#2f6df6` (light) / `#5b8dff` (dark); everything else derives via `color-mix()`
- Rows 21 px compact / 26 px comfortable; column header 26 px with an item count
- Selection: focus = solid accent, ancestor = tinted pill, descendant = dashed ghost
- Ancestors recede by `--recede-amt` (3.2 % light, 4.5 % dark) per level of depth
