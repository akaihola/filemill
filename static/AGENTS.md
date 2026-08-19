# Filemill, static edition — Project Agent Guide

## What this project is

A file manager that browses a **real local folder** in **Miller columns**, and
ships as one self-contained `index.html`. No network, no server, no example
content: the app opens on a folder picker and everything it shows comes from the
directory the user grants, read through the File System Access API.

The UI comes from the "Trail" Miller-columns design study
(originally a filemill design study):
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
│   │   ├── sort.js         ← name/size/mtime order + the getFile() sweep
│   │   ├── render.js       ← buildCol, columnFor, render, preview
│   │   ├── layout.js       ← the fold dial: stripSpan, layout, applyScroll
│   │   ├── trail.js        ← the SVG elbows between columns
│   │   ├── typeahead.js    ← prefix → substring → fuzzy, <mark>, idle buffer
│   │   ├── nav.js          ← choose(), crumbs, copy path, refresh, all keys
│   │   ├── deeplink.js     ← path ⇄ column chain; push-vs-replace policy
│   │   └── settings.js     ← ⚙ popover toggles
│   ├── adapters/           ← everything source-specific
│   │   ├── fsa.js          ← FS: File System Access API      (filemill)
│   │   ├── http.js         ← FS: GET /api/dir                (filemill)
│   │   ├── preview-local.js  ← PREVIEW: text, image, PDF, .desktop
│   │   ├── preview-rich.js   ← PREVIEW: markdown-it/highlight.js/mammoth, on demand
│   │   ├── preview-http.js   ← PREVIEW: GET /api/preview — the Python renderers
│   │   ├── preview-upload.js ← PREVIEW: local bytes → POST /api/render
│   │   ├── router-hash.js  ← ROUTER: #r=root&p=a/b.md        (filemill)
│   │   ├── router-path.js  ← ROUTER: /a/b.md                 (filemill)
│   │   ├── storage.js      ← IndexedDB: remembered folders
│   │   ├── app-fsa.js      ← boot: picker, welcome screen    (filemill)
│   │   └── app-http.js     ← boot: server root + Open local folder…
│   └── vendor/             ← Seti icon map + WOFF font (MIT)
├── filemill/             ← the Python server; see its CONTRIBUTING.md
└── filemill/               ← THIS PROJECT
    ├── AGENTS.md               ← this file
    ├── TASKS.md                ← open task list
    ├── FSA-TEST-CHECKLIST.md   ← what the automated tests cannot check
    ├── index.html              ← GENERATED bundle (do not hand-edit)
    ├── index-dev.html          ← dev entry point: <script src="../ui/…">
    ├── build-index.py          ← index-dev.html + ../ui → index.html
    ├── hotreload.py            ← optional CDP live-patcher for dev mode
    ├── test-ui.py              ← headless suite, fake handle (104 checks)
    ├── test-url.py             ← needs a real origin: deep links, and a real
    │                             filesystem through OPFS (15 checks)
    ├── test-rich.py            ← CDN renderers: offline/switch/loaded (14)
    └── test-e2e.py             ← headed suite, real folder + real picker
```

**Edit `../ui/`, never `index.html`.** The UI is shared with `server/` in
the same repository — a change here is a change there, which is the entire
reason the two live together. Two ways to run what you edited:

```bash
python3 -m http.server 8000 -d ..    # serve the repo root, not static/
#   http://localhost:8000/static/index-dev.html  ← dev, no build step
./build-index.py                     #   → index.html (~149 KB, self-contained)
#   http://localhost:8000/static/index.html      ← the bundle
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
picked roots in the `filemill` database, `kv` store, key `recent`. A record is
the handle **and** the selection chain inside it:

```js
{ handle: FileSystemDirectoryHandle, path: ["notes", "drafts"] }
```

- `rememberRoot(handle[, path])` after every successful pick and, debounced
  400 ms, after every selection change; `isSameEntry()` dedupes. Omit `path`
  and the stored chain is kept, so re-picking a folder does not forget it.
- `recallRoots()` at startup. `queryPermission()` needs no user gesture, so a
  folder still `'granted'` **re-mounts with no dialog at all** — and `mount()`
  walks it back to `recallView()`'s chain, so the return trip costs no clicks.
- `asRoot` reads a bare handle as `{handle, path: []}`, so a database written
  before the chain existed keeps its folders instead of losing all eight.
- Saving hangs off `ROUTER.write` in `app-fsa.js`, which is the one place core
  already reports a selection change. `mounted` is set only when a mount has
  finished, so the mount's own renders cannot overwrite the chain they are
  about to restore.
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

`test-url.py` is separate because it needs a real origin, and two things need
one. `history.pushState` throws on the opaque origin of a `file://` page, which
is the case `test-ui.py` covers. So does `navigator.storage.getDirectory()`,
with `SecurityError: … unsafe for access within a Web application`. It serves
the repo on a loopback port and drives the same fake handle for the links.

**The origin private file system is how this repo tests real files headlessly.**
OPFS hands out a genuine `FileSystemDirectoryHandle` with no folder dialog:
same `entries()`, same `getFile()`, same browser-side plumbing as a picked
folder. `test-url.py` builds 3 000 real files in it (250 at a time; one at a
time takes 25 s) and runs `FSA` against them. That is the only place the cost of
a size sort is visible, because the fake handle answers `getFile()` out of
memory. Measured there at 3 000 files: `entries()` 363–1 117 ms, the sweep
851–1 707 ms (284–569 µs per file), the comparison 18–90 ms. Read the ratio, not
the milliseconds: the sweep lands at 1.5–2.9× the listing in the same run, and
the check asserts that rather than a wall-clock ceiling. What OPFS cannot claim
to be is the user's own disk, which is `test-e2e.py`'s job.

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
Playwright keystrokes; the round-trip dominates. The suite asserts a 100 ms
ceiling at 3 000 entries, which exists to catch the O(entries)-per-keystroke
regression that cost 500–740 ms, not to benchmark a loaded machine. Read the
numbers it prints *relative to each other in the same run*, because absolute
figures move by 3× with load: a type-ahead hit should land near the arrow-key
keystroke it shares a re-render with, and a type-ahead miss well under it.

**End `FAKE` on a value, never on an assignment.** Playwright evaluates the
string and *calls the result if it is a function*, and the result is the
completion value of the last statement. Ending on `window.__spySaves = () => {…}`
handed Playwright that arrow, which it duly invoked — stubbing `recallRoots`
before a single check ran, so two storage checks read an empty list out of a
database that visibly held a record. The trailing `"fake handle ready";` is
load-bearing.

`test-e2e.py` is the only suite that changes a directory, and it changes one it
made itself: `fixture()` builds a folder under the system temp directory and
`owned()` refuses any path outside it, so no check can edit a folder you picked.
It deletes the folder in a `finally`.

A bench that points at the wrong column reports a wonderful number instead of
failing. `__typebench` therefore returns the row count it searched and the check
asserts it — the first version measured the 8-row root column and reported 0 ms,
because `__keybench` had walked the 3 000-entry directory off the path first.

**Assert against a number from the same run, not a wall clock.** An arrow key
at 3 000 entries measured 11.5 to 89.9 ms over 12 runs on one machine and 106 ms
on a slower one. A check that puts a flat 100 ms on that decides by machine load
rather than by code, and it fails for whoever happens to be running something
else. The sort suite therefore compares the keystroke after a sweep against the
arrow key measured in the same run and the same column, allowing the budget as
slack, which is the form the type-ahead check already uses.

**Back a relative timing with an exact assertion.** `arrow + budget` is still
loose enough to hide a re-sort per keystroke, which costs 18–90 ms at this size.
The sort check therefore also asserts something with no clock in it: after 20
presses the focused column is the *same cached entry*. Prove such a pair works
by injecting the regression rather than reasoning about it — a `buildCol` whose
`metaRef` never matches took the keystroke to 569–640 ms against a 109–139 ms
threshold and flipped the identity check false.

Attribution matters more than the totals. Selecting a *file* inside a
3 000-entry directory costs ~60 ms on its own (a preview build plus a
re-render), which swamps anything type-ahead does; the suite therefore measures
an arrow key in that same column for comparison and times `taSearch` separately.
Isolated at 3 000 entries: matching 1.1–1.8 ms, mark plus un-mark 0.07 ms, the
status-strip write 0.01 ms, a whole no-match keystroke 2.3–3.3 ms.

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
| Metadata fetched only on preview, or when a sort asks for it | `getFile()` is a syscall per file: 284 µs each, 851 ms for 3 000 of them, measured against a real filesystem in `test-url.py`. Per row on every open it would stall large directories |
| Sorting by name is the default and reads nothing | The listing already carries the names. Only size and mtime need the sweep, so the expensive path is entered by the option that asked for it and by nothing else |
| The sweep runs from `render()`, over the columns in `path` | No navigation path has to remember to ask, and nothing off screen is read. Opening one folder beside the root reads those two columns, not the tree |
| `ensureMeta` mirrors `FS.ensureLoaded` | One in-flight promise on the node, one writer of the field, so a second render joins the sweep running instead of starting a rival — the same reason `node.loading` exists |
| `columnFor` treats `metaDone` like `kidsRef` | A sweep reorders the rows, so the DOM built before it is no longer the column. Testing it there means a repaint the sweep chose to drop self-heals on the next render, instead of leaving an order that is no longer true |
| A sweep repaints only while its node is still in `path` | It can outlive the column that started it. What it read is kept either way, because a file's size is a fact about that file and stepping back into the folder finds it there |
| Unreadable metadata sorts last in **both** directions | "Biggest first" asks what is biggest; a file the app could not open is not the answer, and putting one at the top is how a permission error gets read as a result. The row is never dropped |
| Directories are never ordered by size or time | No port can give a directory either number: there is no `getFile()` for a directory handle, and the server build's listing sends metadata for files only |
| The sweep catches a rejecting `loadMeta` per row | The port promises to *fill* `node.meta`, not that it never rejects. One escaping rejection would leave `metaLoading` set for good and the column spinning until the tab closed |
| The sort lives in `localStorage`, not the per-folder record | It is how a person reads a list, not a property of the folder. The record also offers no hook: `keepView` fires from `ROUTER.write`, which core calls when the *location* changes, and choosing a sort moves nobody |
| One `Intl.Collator`, not `localeCompare` per call | The comparator runs ~35 000 times per column build at 3 000 entries. Reusing it took ordering 3 000 real files from 116.6 ms to 18.2 ms |
| `pvToken` guards preview fills | A slow read for a file you have navigated away from must not overwrite the current preview |
| Horizontal scroll = fold dial, not translation | `#stage` is sticky so nothing moves; `scrollLeft` is read as 0–100 %. Keeps the preview readable with no manual splitter |
| Column DOM cached per `(node, kids)` in `colCache` | Rebuilding a 3 000-entry column per keystroke cost ~500 ms. Re-renders now only re-apply depth/selection/cursor classes |
| Children reconciled, never `replaceChildren`d | Re-inserting an element detaches it and discards the style + layout of every row under it — that alone was the 500 ms |
| `set()` / `setVar()` write guards | Re-writing the width or a custom property a column already has still relays out all of its rows |
| `content-visibility: auto` on `.row` | Rows have a fixed height, so off-screen ones are skipped: forced layouts (`scrollIntoView`) stop being O(entries) |
| Click handler on `.col`, not just rows | A folded column hides its rows, so "click a spine to unfold" must be handled by the column (the design study advertised this but never wired it) |
| Read-only (`mode: "read"`) | Nothing in the app writes, so never ask for write permission |
| Rich renderers lazy-loaded from a CDN, not bundled | markdown-it + plugins + highlight.js + mammoth are ~1 MB against the app's 140 KB. Fetching them on first use keeps the single file portable and gives it filemill's rendering |
| …but behind a remembered switch, defaulting on | It is the only thing here that talks to the network, and the pitch is that your folder does not. Consent that resets every reload is not consent. Nothing about the file is ever *sent* — the request is for the library |
| Every renderer failure falls back to `PreviewLocal` | Offline must be a loss of fidelity, not a broken pane: raw `<pre>` with a one-line note, or nothing for a binary |
| Version pins on every CDN URL | `@latest` means a preview that renders differently next week, and a dependency that can change under you |
| `core/` + `adapters/`, three ports | The same UI runs over the File System Access API and over a server. filemill browses with `core/` untouched, which is the only way two apps stay identical — a copied UI diverges one bug fix at a time |
| The chrome is built by `core/shell.js`, not written in the HTML | There are two HTML files and the markup has to match in both. A shared *file* would need a build step or a fetch, and the static build can afford neither |
| Hash URLs in the static build, path URLs on the server | A hash survives `file://`, a bare `http.server`, and any static host — none of which can rewrite paths. The server has a root, so its URL path can mirror the file path exactly |
| `#r=<root>` names the folder, matched against the remembered roots | A `FileSystemDirectoryHandle` is not a path: the URL cannot name a folder the browser has not already granted, and a page that could name arbitrary directories would be worse |
| Type-ahead rungs are three passes, not one scored scan | The rungs have to rank across the *whole* column: a name starting with "notes" on row 300 must beat one containing it on row 3. Each pass stops at its own first hit, so an early prefix match never looks at the rest |
| Only the matched row gets `<mark>` | Marking every matching row is an innerHTML write per entry — the O(entries)-per-keystroke cost the column cache exists to avoid. One row is also the honest signal: type-ahead jumps to one place |
| Lower-cased names cached on the column entry (`c.lower`) | Lower-casing 3 000 names costs ~1.4 ms; per keystroke that is most of the search budget. Cached beside `c.kids`, so the two die together and can never disagree |
| A refused clipboard selects the path instead | `writeText` can be refused by policy or context. Failing silently means the next paste hands over something else with nothing to say so; selecting the path puts the browser's own ⌘C one keystroke away, and that one needs no permission |
| The status path joins with `/`, not ` / ` | Clicking it copies it, and the refusal fallback copies the characters on screen. A display string that differs from the copied string makes the fallback quietly wrong |
| History pushes on entering a column, rewrites otherwise | Selecting a folder opens its column without moving focus, so ↑/↓ down a list of folders would otherwise push a history entry per row and make Back useless |
| Refresh empties `node.kids` and re-enters `ensureLoaded` | One loading path, one debounce, one writer of `node.kids`. A separate reload call would be a second writer on the same field, and the interleaving that loses is the one nobody reproduces |
| …but waits for an in-flight read before emptying it | `ensureLoaded` hands a concurrent caller the *in-flight* promise. Invalidating and asking immediately therefore returns the very listing the refresh was called to replace, and looks like a refresh that silently did nothing |
| Nothing renders between invalidating and the read landing | The column cache still holds the old DOM, so the screen keeps the previous listing instead of flashing to "Reading…" and losing its scroll position. The ⟳ spins in place instead |
| No rule in `styles.css` keys off `.col.folding` to hide chrome | `folding` is **not** a transient animation state. `layout.js` sets it on column `folded`, so with nothing scrolled it sits on the *root* column permanently. A `display: none` keyed on it hid the ⟳ on the root for ever, and on whichever column the dial happened to be mid-fold on — which read as two unrelated bugs. Let the header's own opacity crossfade carry anything inside it |
| F5 is claimed; ⌘R, Ctrl+R and Ctrl+F5 are not | Every desktop file manager reads F5 as "re-read this folder", and here a reload costs the mounted root, the column chain and the scroll position. A real reload stays one keystroke away — the rule type-ahead already follows for ⌘R |
| Refreshing a parent re-reads the columns open below it | A re-read hands back new node objects, so the chain has to be matched by name regardless. Those columns are also on screen, and one fresh column beside three stale ones is worse than the extra reads. Closed subtrees are untouched |
| `applyPath` restores refresh, links and remembered folders alike | Three callers, one walk: they cannot disagree about what a half-valid chain means. It stops at the first name that is gone, so no caller can present a selection that is not real |
| The view chain extends the `recent` record, rather than getting its own store | A handle is not a path, so the only honest key for a per-folder store is the handle already sitting in this record. Two stores would also drift the first time one is pruned to 8 and the other is not |
| The chain is stored as names, not nodes | A node comes from a read that has not happened when the page loads. A name outlives a reload, a rename of its parent, and the node cache |
| A truncated restore is saved back truncated | The app remembers where the user actually is. Keeping the deeper chain would mean storing a selection that does not exist, which is the thing both features refuse to display |
| View saves hang off `ROUTER.write`, in the adapter | Core already writes the location on every selection change and nowhere else, so there is nothing to add to core — and the server build has no remembered folders to hook |

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
