# Filemill, static edition — Project Agent Guide

## What this project is

A file manager that browses a **real local folder** in **Miller columns**. It
ships as one self-contained `index.html`. There is no network, no server and
no example content. The app opens on a folder picker. It shows only the
directory that the user grants, read through the File System Access API.

The UI comes from the "Trail" Miller-columns design study: column headers with
counts, three selection states, a drawn trail between selected rows, and
horizontal scroll as a 0–100 % *condensing dial* that folds columns into spines
from the left.

The [repository README](../README.md) describes the two editions and their
shared ports. This document covers the static edition.

---

## Agent memory convention

When the user says "remember X" or "always do Y", or when you find a
project-specific rule worth keeping, **update this file first**. Do the same
for each correction the user makes to your behaviour. The rule then survives a
context reset.

---

## File layout

```
<repo>/
├── README.md               ← what the two editions are, and why one repo
├── .github/workflows/      ← test both, publish index.html to Pages
├── ui/                     ← THE SHARED FRONTEND — a symlink to
│                             server/src/filemill/ui; see ui/adapters/README.md
│   ├── core/               ← source-agnostic: columns, keyboard, preview, links
│   │   ├── styles.css      ← every design token + rule
│   │   ├── shell.js        ← the chrome, so both builds emit the same DOM
│   │   ├── ports.js        ← the FS / PREVIEW / ROUTER seams
│   │   ├── icons.js        ← Seti lookup, folder glyph, esc()
│   │   ├── syntax.js       ← comment/string/number/keyword spans, per language
│   │   ├── state.js        ← globals, visibleKids, measure, fmt*
│   │   ├── sort.js         ← name/size/mtime order + the getFile() sweep
│   │   ├── render.js       ← buildCol, columnFor, render, preview
│   │   ├── layout.js       ← the fold dial: stripSpan, layout, applyScroll
│   │   ├── trail.js        ← the SVG elbows between columns
│   │   ├── typeahead.js    ← prefix → substring → fuzzy, <mark>, idle buffer
│   │   ├── search.js       ← file-content search
│   │   ├── jsonl.js        ← JSON and JSONL as a virtual directory
│   │   ├── nav.js          ← choose(), crumbs, copy path, refresh, all keys
│   │   ├── deeplink.js     ← path ⇄ column chain; push-vs-replace policy
│   │   └── settings.js     ← ⚙ popover toggles
│   ├── adapters/           ← everything source-specific
│   │   ├── fsa.js          ← FS: File System Access API      (static)
│   │   ├── http.js         ← FS: GET /api/dir                (server)
│   │   ├── vfs-csv.js      ← FS: CSV as a virtual directory
│   │   ├── preview-local.js  ← PREVIEW: coloured text, image, PDF, .desktop
│   │   ├── preview-rich.js   ← PREVIEW: markdown-it/mammoth/docutils, on demand
│   │   ├── preview-http.js   ← PREVIEW: GET /api/preview — the Python renderers
│   │   ├── preview-upload.js ← PREVIEW: local bytes → POST /api/render
│   │   ├── router-hash.js  ← ROUTER: #r=root&p=a/b.md        (static)
│   │   ├── router-path.js  ← ROUTER: /a/b.md                 (server)
│   │   ├── storage.js      ← IndexedDB: remembered folders
│   │   ├── app-fsa.js      ← boot: picker, welcome screen    (static)
│   │   └── app-http.js     ← boot: server root + Open local folder…
│   └── vendor/             ← Seti icon map + WOFF font (MIT)
├── server/                 ← the Python server; see its CONTRIBUTING.md
└── static/                 ← THIS PROJECT
    ├── AGENTS.md               ← this file
    ├── FSA-TEST-CHECKLIST.md   ← what the automated tests cannot check
    ├── index.html              ← GENERATED bundle (do not hand-edit)
    ├── index-dev.html          ← dev entry point: loads ../ui/entry-static.js
    ├── build-index.py          ← index-dev.html + the module graph → index.html
    ├── test-ui.py              ← headless suite, fake handle
    ├── test-url.py             ← needs a real origin: deep links, and a real
    │                             filesystem through OPFS
    ├── test-rich.py            ← CDN renderers: offline/switch/loaded
    └── test-e2e.py             ← headed suite, real folder + real picker
```

**Edit `../ui/`, never `index.html`.** The UI is shared with `server/` in the
same repository. A change here is a change there. That is the reason the two
live together.

`../ui/` is a **symlink** to `../server/src/filemill/ui/`. A wheel cannot
reach outside its package, so the shared frontend is inside the server package
and the repository root points at it. There is one copy, so no sync script is
needed. A checkout needs symlink support. Windows needs developer mode for
that.

Two ways to run what you edited:

```bash
python3 -m http.server 8000 -d ..    # serve the repo root, not static/
#   http://localhost:8000/static/index-dev.html  ← dev, no build step
./build-index.py                     #   → index.html (~149 KB, self-contained)
#   http://localhost:8000/static/index.html      ← the bundle
```

`build-index.py` inlines the stylesheet, the icon map and the module graph.
It walks the imports from `../ui/entry-static.js` in the order the browser
evaluates them, removes the `import` lines and the `export` keywords, and
writes the result as one `<script type="module">`. It replaces the
`@font-face` URL with a base64 data URI. It refuses imports it cannot inline:
non-relative specifiers, renames, default and namespace forms.

`./build-index.py --check` exits non-zero when the committed bundle does not
match `../ui/`. CI runs it, because a generated and committed file goes stale
without a check.

---

## Publishing

`.github/workflows/publish.yml` tests every push and deploys `index.html`, and
only that file, to GitHub Pages from `main`.

Pages is the right target for a technical reason. `showDirectoryPicker()`
needs a **secure context**. A downloaded `index.html` opened from disk shows
the `file://` welcome screen instead of a folder picker (see below). An
`https://` page works, so one link gives "browse a local folder, install
nothing". Nothing published can read anything: there is no backend, and the
visitor's browser reads the folder after the visitor grants it.

The workflow runs `playwright install`. That command is **forbidden on the
dev machines**, where browsers come from the Nix store. On a stock CI runner
it is the only way to get them.

---

## Serve it over localhost — `file://` cannot work

Chrome refuses `showDirectoryPicker()` on an opaque origin, which a `file://`
page has. A double-click on `index.html` therefore shows a welcome screen
with instructions instead of a folder. `showBlocked("file")` in `app-fsa.js`
does this, both up front from `location.protocol` and from the
`SecurityError`. This is the most common "it's broken" report.

---

## Remembered folders (IndexedDB)

`FileSystemHandle` is structured-cloneable, so `storage.js` keeps the last 8
picked roots (`RECENT_MAX`) in the `filemill` database, `kv` store, key
`recent`. A record is the handle **and** the selection chain inside it:

```js
{ handle: FileSystemDirectoryHandle, path: ["notes", "drafts"] }
```

- `rememberRoot(handle[, path])` runs after every successful pick and, with a
  400 ms debounce, after every selection change. `isSameEntry()` removes
  duplicates. Omit `path` and the stored chain stays, so a re-pick of a folder
  does not forget it.
- `recallRoots()` runs at startup. `queryPermission()` needs no user gesture,
  so a folder still `'granted'` **re-mounts with no dialog**. `mount()` walks
  it back to `recallView()`'s chain, so the return trip costs no clicks.
- `asRoot` reads a bare handle as `{handle, path: []}`, so a database written
  before the chain existed keeps its folders.
- Saves hang off `ROUTER.write` in `app-fsa.js`, the one place where core
  reports a selection change. `mounted` is set only when a mount has finished,
  so the mount's own renders cannot overwrite the chain they are about to
  restore.
- Otherwise the welcome screen lists the roots under "Recently opened". A
  click calls `requestPermission()` from that gesture. Chrome usually
  downgrades a grant to `'prompt'` when the browser restarts. Expect one
  in-page permission bar per session, and never the OS picker again.

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
network itself. The test aborts `esm.sh` requests to force the offline path.
The loaded path runs against stub modules served from the same loopback port
through `window.FILEMILL_CDN`. `test-ui.py` and `test-url.py` switch rich
previews off, because a failed CDN import logs console errors that hide their
own assertions.

`test-url.py` is separate because it needs a real origin. `history.pushState`
throws on the opaque origin of a `file://` page, which is the case `test-ui.py`
covers. `navigator.storage.getDirectory()` throws there too, with
`SecurityError: … unsafe for access within a Web application`. The test serves
the repo on a loopback port and drives the same fake handle for the links.

**The origin private file system (OPFS) is how this repo tests real files
headlessly.** OPFS gives a real `FileSystemDirectoryHandle` with no folder
dialog: the same `entries()`, `getFile()` and browser-side plumbing as a picked
folder. `test-url.py` builds 3 000 real files in it (250 at a time; one at a
time takes 25 s) and runs `FSA` against them. That is the only place where the
cost of a size sort is visible, because the fake handle answers `getFile()`
from memory. Measured there at 3 000 files: `entries()` 363–1 117 ms, the
sweep 851–1 707 ms (284–569 µs per file), the comparison 18–90 ms. Read the
ratio, not the milliseconds. The sweep lands at 1.5–2.9× the listing in the
same run, and the check asserts that ratio, not a wall-clock ceiling. OPFS is
not the user's own disk. That is `test-e2e.py`'s job.

**Never run `playwright install`.** Pin the version that matches the
NixOS-installed browsers. Now that is rev 1228 → `playwright==1.61.0`, which
is also what `$UV_CONSTRAINT` says.

`test-ui.py` fakes the handle API, which is all the app touches:

```js
const D = (name, kids) => ({kind:'directory', name,
  entries: async function*(){ for (const k of kids) yield [k.name, k]; }});
const F = (name, text) => ({kind:'file', name,
  getFile: async () => new File([text], name, {lastModified: Date.now()})});
mount(D('workspace', [D('src', [F('app.py', 'print(1)')]), F('README.md', '# hi')]));
```

A `file://` page is fine for it, because `mount(fake)` bypasses the picker.
Measure render cost **in-page** (`performance.now()` around `render()`), never
by timing Playwright keystrokes. The round trip dominates. The suite asserts a
100 ms ceiling at 3 000 entries. The ceiling catches the O(entries)-per-keystroke
regression that cost 500–740 ms. It does not benchmark a loaded machine. Read
the printed numbers *relative to each other in the same run*, because absolute
figures move by 3× with load. A type-ahead hit must land near the arrow-key
keystroke it shares a re-render with, and a type-ahead miss well under it.

**End `FAKE` on a value, never on an assignment.** Playwright evaluates the
string and *calls the result if it is a function*. The result is the completion
value of the last statement. Ending on `window.__spySaves = () => {…}` gave
Playwright that arrow function, which it invoked. That stubbed `recallRoots`
before a single check ran, so two storage checks read an empty list from a
database that held a record. The trailing `"fake handle ready";` is
load-bearing.

`test-e2e.py` is the only suite that changes a directory, and it changes one
it made itself. `fixture()` builds a folder under the system temp directory.
`owned()` refuses any path outside it, so no check can edit a folder you
picked. The suite deletes the folder in a `finally`.

A bench that points at the wrong column reports a good number instead of a
failure. `__typebench` therefore returns the row count it searched, and the
check asserts it. The first version measured the 8-row root column and
reported 0 ms, because `__keybench` had walked the 3 000-entry directory off
the path first.

**Assert against a number from the same run, not a wall clock.** An arrow key
at 3 000 entries measured 11.5 to 89.9 ms over 12 runs on one machine and 106
ms on a slower one. A flat 100 ms limit decides by machine load, not by code,
and fails for whoever runs something else. The sort suite therefore compares
the keystroke after a sweep against the arrow key measured in the same run and
the same column, with the budget as slack. The type-ahead check uses the same
form.

**Back a relative timing with an exact assertion.** `arrow + budget` can still
hide a re-sort per keystroke, which costs 18–90 ms at this size. The sort check
therefore also asserts something with no clock in it: after 20 presses the
focused column is the *same cached entry*. Prove such a pair works by injecting
the regression. A `buildCol` whose `metaRef` never matches took the keystroke
to 569–640 ms against a 109–139 ms threshold and flipped the identity check to
false.

Attribution matters more than the totals. Selecting a *file* in a 3 000-entry
directory costs about 60 ms on its own (a preview build plus a re-render). That
hides anything type-ahead does. The suite therefore measures an arrow key in
the same column for comparison and times `taSearch` separately. Isolated at
3 000 entries: matching 1.1–1.8 ms, mark plus un-mark 0.07 ms, the status-strip
write 0.01 ms, a whole no-match keystroke 2.3–3.3 ms.

---

## Key design decisions

- [0003-modular-src-generated-index-html](../docs/adr/0003-modular-src-generated-index-html.md) — Modular `src/`, generated `index.html`
- [0004-focus-follows-the-selection-not-the-newest-column](../docs/adr/0004-focus-follows-the-selection-not-the-newest-column.md) — Focus follows the *selection*, not the newest column
- [0005-node-lastsel-per-directory](../docs/adr/0005-node-lastsel-per-directory.md) — `node.lastSel` per directory
- [0006-folder-picker-as-a-full-screen-welcome-state](../docs/adr/0006-folder-picker-as-a-full-screen-welcome-state.md) — Folder picker as a full-screen welcome state
- [0007-kids-null-means-not-read-yet](../docs/adr/0007-kids-null-means-not-read-yet.md) — `kids === null` means "not read yet"
- [0008-node-loading-promise-awaited-by-concurrent-callers](../docs/adr/0008-node-loading-promise-awaited-by-concurrent-callers.md) — `node.loading` promise, awaited by concurrent callers
- [0009-metadata-fetched-only-on-preview-or-when-a-sort-asks-for-it](../docs/adr/0009-metadata-fetched-only-on-preview-or-when-a-sort-asks-for-it.md) — Metadata fetched only on preview, or when a sort asks for it
- [0010-sorting-by-name-is-the-default-and-reads-nothing](../docs/adr/0010-sorting-by-name-is-the-default-and-reads-nothing.md) — Sorting by name is the default and reads nothing
- [0011-the-sweep-runs-from-render-over-the-columns-in-path](../docs/adr/0011-the-sweep-runs-from-render-over-the-columns-in-path.md) — The sweep runs from `render()`, over the columns in `path`
- [0012-ensuremeta-mirrors-fs-ensureloaded](../docs/adr/0012-ensuremeta-mirrors-fs-ensureloaded.md) — `ensureMeta` mirrors `FS.ensureLoaded`
- [0013-columnfor-treats-metadone-like-kidsref](../docs/adr/0013-columnfor-treats-metadone-like-kidsref.md) — `columnFor` treats `metaDone` like `kidsRef`
- [0014-a-sweep-repaints-only-while-its-node-is-still-in-path](../docs/adr/0014-a-sweep-repaints-only-while-its-node-is-still-in-path.md) — A sweep repaints only while its node is still in `path`
- [0015-unreadable-metadata-sorts-last-in-both-directions](../docs/adr/0015-unreadable-metadata-sorts-last-in-both-directions.md) — Unreadable metadata sorts last in **both** directions
- [0016-directories-are-never-ordered-by-size-or-time](../docs/adr/0016-directories-are-never-ordered-by-size-or-time.md) — Directories are never ordered by size or time
- [0017-the-sweep-catches-a-rejecting-loadmeta-per-row](../docs/adr/0017-the-sweep-catches-a-rejecting-loadmeta-per-row.md) — The sweep catches a rejecting `loadMeta` per row
- [0018-the-sort-lives-in-localstorage-not-the-per-folder-record](../docs/adr/0018-the-sort-lives-in-localstorage-not-the-per-folder-record.md) — The sort lives in `localStorage`, not the per-folder record
- [0019-one-intl-collator-not-localecompare-per-call](../docs/adr/0019-one-intl-collator-not-localecompare-per-call.md) — One `Intl.Collator`, not `localeCompare` per call
- [0020-pvtoken-guards-preview-fills](../docs/adr/0020-pvtoken-guards-preview-fills.md) — `pvToken` guards preview fills
- [0021-horizontal-scroll-fold-dial-not-translation](../docs/adr/0021-horizontal-scroll-fold-dial-not-translation.md) — Horizontal scroll = fold dial, not translation
- [0022-the-dial-s-resting-place-never-folds-the-focused-column-nor-anything-r](../docs/adr/0022-the-dial-s-resting-place-never-folds-the-focused-column-nor-anything-r.md) — The dial's resting place never folds the focused column, nor anything right of it
- [0023-so-a-column-right-of-focus-may-overflow-the-finder-and-only-its-left-e](../docs/adr/0023-so-a-column-right-of-focus-may-overflow-the-finder-and-only-its-left-e.md) — …so a column right of focus may overflow the finder, and only its left edge is promised
- [0024-and-when-the-touched-column-would-overflow-the-strip-pans-left](../docs/adr/0024-and-when-the-touched-column-would-overflow-the-strip-pans-left.md) — …and when the *touched* column would overflow, the strip pans left
- [0025-no-column-is-wider-than-the-screen-it-sits-on](../docs/adr/0025-no-column-is-wider-than-the-screen-it-sits-on.md) — No column is wider than the screen it sits on
- [0026-measured-on-finder-never-on-stage](../docs/adr/0026-measured-on-finder-never-on-stage.md) — …measured on `#finder`, never on `#stage`
- [0027-revealrow-scrolls-the-column-body-never-scrollintoview](../docs/adr/0027-revealrow-scrolls-the-column-body-never-scrollintoview.md) — `revealRow` scrolls the column body, never `scrollIntoView`
- [0028-and-applyscroll-pins-stage-scrollleft-to-0-anyway](../docs/adr/0028-and-applyscroll-pins-stage-scrollleft-to-0-anyway.md) — …and `applyScroll` pins `stage.scrollLeft` to 0 anyway
- [0029-column-dom-cached-per-node-kids-in-colcache](../docs/adr/0029-column-dom-cached-per-node-kids-in-colcache.md) — Column DOM cached per `(node, kids)` in `colCache`
- [0030-children-reconciled-never-replacechildren-d](../docs/adr/0030-children-reconciled-never-replacechildren-d.md) — Children reconciled, never `replaceChildren`d
- [0031-set-setvar-write-guards](../docs/adr/0031-set-setvar-write-guards.md) — `set()` / `setVar()` write guards
- [0032-content-visibility-auto-on-row](../docs/adr/0032-content-visibility-auto-on-row.md) — `content-visibility: auto` on `.row`
- [0033-click-handler-on-col-not-just-rows](../docs/adr/0033-click-handler-on-col-not-just-rows.md) — Click handler on `.col`, not just rows
- [0034-read-only-mode-read](../docs/adr/0034-read-only-mode-read.md) — Read-only (`mode: "read"`)
- [0035-rich-renderers-lazy-loaded-from-a-cdn-not-bundled](../docs/adr/0035-rich-renderers-lazy-loaded-from-a-cdn-not-bundled.md) — Rich renderers lazy-loaded from a CDN, not bundled
- [0036-but-behind-a-remembered-switch-defaulting-on](../docs/adr/0036-but-behind-a-remembered-switch-defaulting-on.md) — …but behind a remembered switch, defaulting on
- [0037-syntax-highlighting-in-the-page-core-syntax-js-not-from-pygments-or-a-](../docs/adr/0037-syntax-highlighting-in-the-page-core-syntax-js-not-from-pygments-or-a-.md) — Syntax highlighting in the page (`core/syntax.js`), not from Pygments or a CDN
- [0038-a-text-preview-is-whole-or-absent-text-max-512-kb-is-the-only-limit](../docs/adr/0038-a-text-preview-is-whole-or-absent-text-max-512-kb-is-the-only-limit.md) — A text preview is whole or absent; `TEXT_MAX` (512 KB) is the only limit
- [0039-every-renderer-failure-falls-back-to-previewlocal](../docs/adr/0039-every-renderer-failure-falls-back-to-previewlocal.md) — Every renderer failure falls back to `PreviewLocal`
- [0040-version-pins-on-every-cdn-url](../docs/adr/0040-version-pins-on-every-cdn-url.md) — Version pins on every CDN URL
- [0041-core-adapters-three-ports](../docs/adr/0041-core-adapters-three-ports.md) — `core/` + `adapters/`, three ports
- [0042-the-chrome-is-built-by-core-shell-js-not-written-in-the-html](../docs/adr/0042-the-chrome-is-built-by-core-shell-js-not-written-in-the-html.md) — The chrome is built by `core/shell.js`, not written in the HTML
- [0043-hash-urls-in-the-static-build-path-urls-on-the-server](../docs/adr/0043-hash-urls-in-the-static-build-path-urls-on-the-server.md) — Hash URLs in the static build, path URLs on the server
- [0044-r-root-names-the-folder-matched-against-the-remembered-roots](../docs/adr/0044-r-root-names-the-folder-matched-against-the-remembered-roots.md) — `#r=<root>` names the folder, matched against the remembered roots
- [0045-type-ahead-rungs-are-three-passes-not-one-scored-scan](../docs/adr/0045-type-ahead-rungs-are-three-passes-not-one-scored-scan.md) — Type-ahead rungs are three passes, not one scored scan
- [0046-only-the-matched-row-gets-mark](../docs/adr/0046-only-the-matched-row-gets-mark.md) — Only the matched row gets `<mark>`
- [0047-lower-cased-names-cached-on-the-column-entry-c-lower](../docs/adr/0047-lower-cased-names-cached-on-the-column-entry-c-lower.md) — Lower-cased names cached on the column entry (`c.lower`)
- [0048-a-refused-clipboard-selects-the-path-instead](../docs/adr/0048-a-refused-clipboard-selects-the-path-instead.md) — A refused clipboard selects the path instead
- [0049-the-status-path-joins-with-not](../docs/adr/0049-the-status-path-joins-with-not.md) — The status path joins with `/`, not ` / `
- [0050-history-pushes-on-entering-a-column-rewrites-otherwise](../docs/adr/0050-history-pushes-on-entering-a-column-rewrites-otherwise.md) — History pushes on entering a column, rewrites otherwise
- [0051-refresh-empties-node-kids-and-re-enters-ensureloaded](../docs/adr/0051-refresh-empties-node-kids-and-re-enters-ensureloaded.md) — Refresh empties `node.kids` and re-enters `ensureLoaded`
- [0052-but-waits-for-an-in-flight-read-before-emptying-it](../docs/adr/0052-but-waits-for-an-in-flight-read-before-emptying-it.md) — …but waits for an in-flight read before emptying it
- [0053-nothing-renders-between-invalidating-and-the-read-landing](../docs/adr/0053-nothing-renders-between-invalidating-and-the-read-landing.md) — Nothing renders between invalidating and the read landing
- [0054-no-rule-in-styles-css-keys-off-col-folding-to-hide-chrome](../docs/adr/0054-no-rule-in-styles-css-keys-off-col-folding-to-hide-chrome.md) — No rule in `styles.css` keys off `.col.folding` to hide chrome
- [0055-f5-is-claimed-r-ctrl-r-and-ctrl-f5-are-not](../docs/adr/0055-f5-is-claimed-r-ctrl-r-and-ctrl-f5-are-not.md) — F5 is claimed; ⌘R, Ctrl+R and Ctrl+F5 are not
- [0056-refreshing-a-parent-re-reads-the-columns-open-below-it](../docs/adr/0056-refreshing-a-parent-re-reads-the-columns-open-below-it.md) — Refreshing a parent re-reads the columns open below it
- [0057-applypath-restores-refresh-links-and-remembered-folders-alike](../docs/adr/0057-applypath-restores-refresh-links-and-remembered-folders-alike.md) — `applyPath` restores refresh, links and remembered folders alike
- [0058-the-view-chain-extends-the-recent-record-rather-than-getting-its-own-s](../docs/adr/0058-the-view-chain-extends-the-recent-record-rather-than-getting-its-own-s.md) — The view chain extends the `recent` record, rather than getting its own store
- [0059-the-chain-is-stored-as-names-not-nodes](../docs/adr/0059-the-chain-is-stored-as-names-not-nodes.md) — The chain is stored as names, not nodes
- [0060-a-truncated-restore-is-saved-back-truncated](../docs/adr/0060-a-truncated-restore-is-saved-back-truncated.md) — A truncated restore is saved back truncated
- [0061-view-saves-hang-off-router-write-in-the-adapter](../docs/adr/0061-view-saves-hang-off-router-write-in-the-adapter.md) — View saves hang off `ROUTER.write`, in the adapter

---

## Visual spec

All of it is CSS custom properties at the top of `../ui/core/styles.css`.
Change the tokens, not the rules. `data-theme="light|dark"` and
`data-density="compact|comfortable"` on `<html>` switch whole palettes and
metrics. Both come from the ⚙ popover.

- Accent `#2f6df6` (light) / `#5b8dff` (dark); everything else derives via `color-mix()`
- Rows 21 px compact / 26 px comfortable; column header 26 px with an item count
- Selection: focus = solid accent, ancestor = tinted pill, descendant = dashed ghost
- Ancestors recede by `--recede-amt` (3.2 % light, 4.5 % dark) per level of depth
