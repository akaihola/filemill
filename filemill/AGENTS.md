# filemill — Project Agent Guide

## What this project is

A file manager that browses a **real local folder** in **Miller columns**, and
ships as one self-contained `index.html`. No network, no server, no example
content: the app opens on a folder picker and everything it shows comes from the
directory the user grants, read through the File System Access API.

The UI comes from the "Trail" Miller-columns design study
(originally a pykofinder design study):
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
<repo>/
├── README.md               ← what the two projects are, and why one repo
├── .github/workflows/      ← test both, publish filemill to Pages
├── ui/                     ← THE SHARED FRONTEND — see ui/adapters/README.md
│   ├── core/               ← source-agnostic: columns, keyboard, preview, links
│   │   ├── styles.css      ← every design token + rule
│   │   ├── shell.js        ← the chrome, so both builds emit the same DOM
│   │   ├── ports.js        ← the FS / PREVIEW / ROUTER seams
│   │   ├── icons.js        ← Seti lookup, folder glyph, esc()
│   │   ├── state.js        ← globals, visibleKids, measure, fmt*
│   │   ├── render.js       ← buildCol, columnFor, render, preview
│   │   ├── layout.js       ← the fold dial: stripSpan, layout, applyScroll
│   │   ├── trail.js        ← the SVG elbows between columns
│   │   ├── nav.js          ← choose(), crumbs, all keyboard handling
│   │   ├── deeplink.js     ← path ⇄ column chain; push-vs-replace policy
│   │   └── settings.js     ← ⚙ popover toggles
│   ├── adapters/           ← everything source-specific
│   │   ├── fsa.js          ← FS: File System Access API      (filemill)
│   │   ├── http.js         ← FS: GET /api/dir                (pykofinder)
│   │   ├── preview-local.js  ← PREVIEW: text, image, PDF, .desktop
│   │   ├── preview-rich.js   ← PREVIEW: markdown-it/highlight.js/mammoth, on demand
│   │   ├── preview-http.js   ← PREVIEW: GET /api/preview — the Python renderers
│   │   ├── preview-upload.js ← PREVIEW: local bytes → POST /api/render
│   │   ├── router-hash.js  ← ROUTER: #r=root&p=a/b.md        (filemill)
│   │   ├── router-path.js  ← ROUTER: /a/b.md                 (pykofinder)
│   │   ├── storage.js      ← IndexedDB: remembered folders
│   │   ├── app-fsa.js      ← boot: picker, welcome screen    (filemill)
│   │   └── app-http.js     ← boot: server root + Open local folder…
│   └── vendor/             ← Seti icon map + WOFF font (MIT)
├── pykofinder/             ← the Python server; see its CONTRIBUTING.md
└── filemill/               ← THIS PROJECT
    ├── AGENTS.md               ← this file
    ├── TASKS.md                ← open task list
    ├── FSA-TEST-CHECKLIST.md   ← what the automated tests cannot check
    ├── index.html              ← GENERATED bundle (do not hand-edit)
    ├── index-dev.html          ← dev entry point: <script src="../ui/…">
    ├── build-index.py          ← index-dev.html + ../ui → index.html
    ├── hotreload.py            ← optional CDP live-patcher for dev mode
    ├── test-ui.py              ← headless suite, fake handle (31 checks)
    ├── test-url.py             ← deep-link suite over localhost (12 checks)
    ├── test-rich.py            ← CDN renderers: offline/switch/loaded (14)
    └── test-e2e.py             ← headed suite, real folder + real picker
```

**Edit `../ui/`, never `index.html`.** The UI is shared with `pykofinder/` in
the same repository — a change here is a change there, which is the entire
reason the two live together. Two ways to run what you edited:

```bash
python3 -m http.server 8000 -d ..    # serve the repo root, not filemill/
#   http://localhost:8000/filemill/index-dev.html  ← dev, no build step
./build-index.py                     #   → index.html (~149 KB, self-contained)
#   http://localhost:8000/filemill/index.html      ← the bundle
```

`build-index.py` inlines each `<link rel=stylesheet>` and `<script src>` the
browser would have fetched, and swaps the `@font-face` URL for a base64 data
URI — the same trick the old `build.py` used, extended to cover the font.

`./build-index.py --check` exits non-zero when the committed bundle no longer
matches `src/`. CI runs it, because a generated-and-committed file is exactly
the kind that gets published a week stale.

---

## Publishing

`.github/workflows/publish.yml` tests every push and deploys `index.html` — and
only that file — to GitHub Pages from `main`.

Pages is the right target for a reason beyond convenience: `showDirectoryPicker()`
needs a **secure context**, so a downloaded `index.html` opened from disk hits
the `file://` welcome screen instead of a folder picker (see below). An
`https://` page just works, which turns "browse a local folder, install nothing"
into one link. Nothing published can read anything — there is no backend, and
the folder is read in the visitor's browser after they grant it.

Note the workflow runs `playwright install`, which is **forbidden on the dev
machines** where browsers come from the Nix store; on a stock CI runner it is
the only way to get them.

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
uv run --with "playwright==1.61.0" python3 test-url.py         # deep links
uv run --with "playwright==1.61.0" python3 test-url.py --dev
uv run --with "playwright==1.61.0" python3 test-rich.py        # CDN renderers
uv run --with "playwright==1.61.0" python3 test-rich.py --dev
uv run --with "playwright==1.61.0" python3 test-e2e.py         # real folder
```

`test-rich.py` covers the only feature that touches the network. It needs no
network itself: the offline path is the sandbox's natural state, and the loaded
path runs against stub modules served from the same loopback port via
`window.FILEMILL_CDN`. `test-ui.py` and `test-url.py` switch rich previews off,
because a failed CDN import logs console errors that would drown their own
assertions.

`test-url.py` is separate because it needs a real origin: `history.pushState`
throws on the opaque origin of a `file://` page, which is the case `test-ui.py`
covers. It serves the repo on a loopback port and drives the same fake handle.

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
| Rich renderers lazy-loaded from a CDN, not bundled | markdown-it + plugins + highlight.js + mammoth are ~1 MB against the app's 140 KB. Fetching them on first use keeps the single file portable and gives it pykofinder's rendering |
| …but behind a remembered switch, defaulting on | It is the only thing here that talks to the network, and the pitch is that your folder does not. Consent that resets every reload is not consent. Nothing about the file is ever *sent* — the request is for the library |
| Every renderer failure falls back to `PreviewLocal` | Offline must be a loss of fidelity, not a broken pane: raw `<pre>` with a one-line note, or nothing for a binary |
| Version pins on every CDN URL | `@latest` means a preview that renders differently next week, and a dependency that can change under you |
| `core/` + `adapters/`, three ports | The same UI runs over the File System Access API and over a server. pykofinder browses with `core/` untouched, which is the only way two apps stay identical — a copied UI diverges one bug fix at a time |
| The chrome is built by `core/shell.js`, not written in the HTML | There are two HTML files and the markup has to match in both. A shared *file* would need a build step or a fetch, and the static build can afford neither |
| Hash URLs in the static build, path URLs on the server | A hash survives `file://`, a bare `http.server`, and any static host — none of which can rewrite paths. The server has a root, so its URL path can mirror the file path exactly |
| `#r=<root>` names the folder, matched against the remembered roots | A `FileSystemDirectoryHandle` is not a path: the URL cannot name a folder the browser has not already granted, and a page that could name arbitrary directories would be worse |
| History pushes on entering a column, rewrites otherwise | Selecting a folder opens its column without moving focus, so ↑/↓ down a list of folders would otherwise push a history entry per row and make Back useless |

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
