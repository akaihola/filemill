# PLAN-20 — One frontend for Pykofinder and Filemill

> **Historical.** Written while these were two projects: *filemill*, the static
> HTML explorer, and *pykofinder*, the Python server. They are now one
> repository and one product — `static/` and `server/` editions of **Filemill**
> — so read every "pykofinder" below as the server edition and every "filemill"
> as the static one. The document is left in the names it was written in
> because a plan rewritten to match the outcome stops being a record of it.

Status: **implemented, except the cutover (step 7) and mobile.** See §7 for the
per-step state. Two decisions went against this document and are marked there:
the repo merge does not delete the vendoring script (§7.1), and rich rendering
is CDN-loaded rather than a second build profile (§7.8, overriding §4b). The
analysis below is otherwise unchanged from the proposal.

Scope: how to share as much code as possible between `filemill` (static
single-HTML, File System Access API) and `pykofinder` (FastHTML server) as
Pykofinder migrates to the Miller-columns UI, and whether to merge the repos.

---

## 1 · Where the two stand today

| | filemill | pykofinder |
| --- | --- | --- |
| UI | Miller columns, fold dial, trail elbows, ⚙ popover — the productionised "Trail" study | old Finder-style columns, server-rendered |
| Rendering | client-side JS, `src/*.js` (~1 100 lines incl. CSS) | server-side Python → HTML fragments, HTMX swaps |
| Navigation | in-memory `path[]` / `sel[]`, keyboard in `nav.js` | HTMX `/click`, `/restore`, keyboard IIFE inside `styles.py` |
| Data source | `FileSystemDirectoryHandle` (FSA) | real filesystem + VFS providers (SQLite/JSON/CSV) |
| Previews | `<pre>` text + `<img>` only | markdown-it-py + plugins, Pygments, mammoth, python-pptx, PDF iframe, `.desktop` |
| URLs | none — reload loses everything | canonical `/f/<mount>/<path>`, deep-link restore, PWA |
| Ship | `build-index.py` → one 117 KB `index.html` | `uv run pykofinder`, PyPI package |

The valuable, non-overlapping assets are: **filemill's UI** and **pykofinder's
Python rendering + VFS + URL model**. Nothing about the first depends on the
second, and vice versa — which is why this is worth doing.

---

## 2 · The core finding: filemill already has exactly one seam

The Miller-columns UI touches a node through a very narrow interface. Grepping
`render.js`, `nav.js`, `state.js`, `layout.js`, `trail.js` for node access, the
*entire* contract is:

```js
node.name          // string
node.dir           // boolean
node.kids          // null = unread · [] = empty/denied · [Node] = read
node.denied        // string, optional
node.lastSel       // UI scratch, written by the UI itself
ensureLoaded(node) // → Promise, fills node.kids
loadMeta(node)     // → fills node.meta = {size, mod, type} and node.file
node.file          // Blob, only used by fillPreview()
```

That is *all* of `src/fs.js` (50 lines). Everything else — `state.js`,
`render.js`, `layout.js`, `trail.js`, `nav.js`, `settings.js`, `icons.js`,
`styles.css`, roughly 95 % of the frontend — is source-agnostic and can run
unmodified against a server.

So the sharing story is not "extract a component library". It is:

> **One UI core. Three small adapters: filesystem, preview, router.**

### Adapter 1 — filesystem

```js
// filemill: today's fs.js, unchanged
// pykofinder: same shape, HTTP-backed
async function ensureLoaded(node) {
  if (!node.dir || node.kids !== null) return;
  node.loading ??= fetch(`/api/dir?p=${enc(node.path)}`)
    .then(r => r.json())
    .then(j => { node.kids = j.entries.map(mkNode); node.denied = j.denied; });
  return node.loading;
}
```

The server adapter is *easier* than the FSA one: one round-trip returns names,
`dir` flags, sizes and mtimes together, so `loadMeta` becomes a no-op and the
"metadata only on preview" concession disappears. Sort options (filemill
TASKS.md, currently blocked on a `getFile()` sweep) become free on the server
side.

VFS drops in with no UI change at all: a SQLite table is just a node with
`dir: true` and a `vpath`, since the renderer never looks past `name`/`dir`/
`kids`. `icons.js` only needs an optional `node.icon` override for VFS glyphs.

### Adapter 2 — preview

`fillPreview()` in `render.js` currently hard-codes two regexes and produces
HTML inline. Replace with a provider:

```js
previewProvider.render(node) → Promise<{html, kind}>
```

- **Pykofinder**: `fetch('/api/preview?p=…')` → the existing `preview.py`
  output verbatim. Markdown-it-py plugins, Pygments, mammoth, python-pptx,
  wikilinks, Mermaid — all of it, unchanged, zero porting.
- **Filemill**: JS renderers (§4), or the lean text/image fallback that exists
  today.

The preview pane's chrome (hero, meta `<dl>`, `pvToken` race guard) stays
shared; only the body fragment differs.

### Adapter 3 — router

See §5. Today filemill has none and Pykofinder has a good one.

---

## 3 · What Pykofinder gains, beyond the UI

**"Open local folder…" is nearly free.** Once the UI is adapter-driven, the
Pykofinder page can carry *both* adapters and switch at runtime: server-backed
by default, FSA-backed when the user picks a local folder. Same page, same
keyboard model, same styles. This is the single strongest argument for one
codebase rather than two lookalikes.

**And the previews still work for local folders.** The obvious objection —
"the server can't read the folder the browser granted" — has a clean answer:
`POST /api/render` with the file bytes, get back the same Python-rendered
fragment. Same origin, localhost, the user already granted the folder. Cost is
one POST per preview on loopback, which is nothing, with a size cap.

> **Consequence: Pykofinder never needs the JS renderers at all**, even in
> local-folder mode. The JS renderer work is *purely* a filemill concern, and
> can be deferred without blocking the migration.

**Deletions.** `columns.py` (346 lines), the HTMX/keyboard/CSS blob in
`styles.py` (1 035 lines), `/click`, `/restore`, `_build_prune_js`, the OOB
breadcrumb machinery — most of it goes. `preview.py`, `rendering.py`, `vfs.py`,
`providers/`, `_resolve_safe()` survive and are the parts worth keeping.

---

## 4 · The renderer question — Python vs JS

Three options, and the answer differs per project.

### 4a · Client-side Python (Pyodide) — **reject**

~10 MB runtime plus wheels for pygments/mammoth/python-pptx/lxml, multi-second
cold start, and it destroys the one thing filemill is for: a single portable
HTML file. Not viable.

### 4b · JS renderers for filemill — **recommended, and cheaper than it looks**

Pykofinder's Python stack is, for the most part, *ports of JS libraries*:

| Pykofinder (Python) | JS equivalent | Note |
| --- | --- | --- |
| `markdown-it-py` + `mdit-py-plugins` | `markdown-it` + `markdown-it-*` | markdown-it is the **upstream**; same plugin names, same API, same output |
| `mammoth` (docx) | `mammoth.js` | same author, JS is the original |
| `python-pptx` (text only) | JSZip + XML parse | current preview extracts text only — ~100 lines reaches parity |
| Pygments "friendly" | `highlight.js` / Shiki | different token classes; needs a CSS theme mapping |
| PDF iframe on `/raw` | iframe on a blob URL | Chromium renders it natively — no pdf.js needed |
| Mermaid | Mermaid (same lib) | ~2.5 MB; make it opt-in |

So parity is genuinely reachable, and for Markdown it is *byte-identical
output* if the same plugin set is configured. The real friction is only
Pygments↔highlight.js class names — solved by shipping one stylesheet per
highlighter rather than trying to make one match the other.

**Bundle size is the actual constraint.** Rough minified figures (verify before
committing to them): markdown-it + plugins ~150 KB, highlight.js common ~120 KB,
mammoth.js ~500 KB, JSZip ~100 KB. A "fat" filemill lands near 1 MB versus
today's 117 KB.

Answer: **two build targets from one source.**

```
build.py --profile lean  → filemill.html       (~120 KB, text + image previews)
build.py --profile full  → filemill-full.html  (~1 MB, md/code/docx/pptx)
```

Do *not* lazy-load renderers from a CDN — that breaks the "no network" promise
that makes the single file worth shipping.

### 4c · Keep Python server-side only — **the Pykofinder answer**

Per §3, this is already true and requires no work.

---

## 5 · URLs and deep links

This is the third seam, and the shared part is bigger than it looks. Both
projects need the same function:

```js
// walk the chain from root, loading each directory, select the leaf
async function applyPath(relPath)   // "src/pykofinder/app.py" → path[]/sel[]/focusCol
function currentPath()              // path[]/sel[] → "src/pykofinder/app.py"
```

`applyPath` is shared verbatim; it is exactly what Pykofinder's `/restore` does
today in Python, and it is entirely missing from filemill. Only the *transport*
differs:

**Pykofinder** — `history.pushState` on the real path, mirroring the file path
relative to root, exactly as PLAN-19 specifies:

```
/src/pykofinder/app.py
/src/pykofinder/app.py?filemill=highlight
```

Query params carry representation/layout/dotfiles; the path carries only the
file. The existing canonical-URL work and `_resolve_safe()` validation both
carry over.

**Filemill** — hash, not query string: it survives `file://`, needs no server
config on any static host, and never round-trips to a server that isn't there.

```
#p=/src/main.js
#r=3&p=/src/main.js       ← r = IndexedDB id of the remembered root
```

The `r` key is needed because an FSA handle is not a path — the URL cannot name
a folder the browser has not granted. On load: look up root `r` in the existing
`storage.js` `recent` list, `queryPermission()`, and if granted, `applyPath(p)`
with no dialog. If not granted, show the welcome screen with the target
remembered and apply it after the click. This composes cleanly with the
remembered-folders machinery that already exists.

A single `router.js` with `serverRouter` / `hashRouter` behind
`{ read(), write(state), onNavigate(cb) }` covers both.

---

## 6 · Repo strategy — merge

Three options considered:

1. **One repo, shared `ui/`** — recommended.
2. Separate repos, `ui/` as a git submodule or subtree.
3. Pykofinder vendors filemill's built `index.html`.

Option 3 is out: Pykofinder needs the *modular* source to swap adapters, not
the bundle. Option 2 is the usual submodule tax — two clones, two branches, and
a lockstep-bump ritual for every UI change, which is most changes.

The failure mode this whole plan exists to prevent is **drift** — two
near-identical UIs diverging one bug fix at a time. A submodule only makes drift
slower, not impossible; one repo makes it structurally impossible. Both projects
have the same author and the same release cadence, so the usual reasons to split
(independent teams, independent versioning) do not apply.

```
finder/                       ← merged repo
├── ui/
│   ├── core/                 ← state, render, layout, trail, nav, settings,
│   │                           icons, routing, styles.css  (source-agnostic)
│   ├── adapters/
│   │   ├── fsa.js            ← File System Access API
│   │   ├── http.js           ← fetch /api/dir, /api/preview
│   │   ├── preview-js.js     ← markdown-it, highlight.js, mammoth, jszip
│   │   └── preview-http.js   ← server fragments
│   ├── router/{hash.js,history.js}
│   ├── index.html            ← build-free dev entry point
│   └── tests/                ← the Playwright suite, one copy, both adapters
├── filemill/
│   └── build.py              ← ui/ + profile → filemill.html
└── pykofinder/               ← the Python package, published to PyPI
    ├── pyproject.toml
    └── src/pykofinder/       ← app.py (JSON API), preview.py, rendering.py,
                                vfs.py, providers/
```

Pykofinder serves `ui/` as static assets in dev and embeds it at wheel-build
time, so the PyPI artifact stays self-contained. Filemill's single-file
deliverable is a build target in the same tree — "publish the static HTML"
becomes one command in CI, which is the other thing the merge buys.

Mechanically: `git subtree`/`git remote add` + merge preserves both histories;
neither project's history needs to be discarded.

---

## 7 · Migration sequence

Each step leaves both apps working.

1. ✅ **Merge the repos** — subtree merge preserving both histories, then
   `ui/` + `static/` + `server/` (named `filemill/` and `pykofinder/` at the
   time). `tools/sync-ui.py` survives but changes
   meaning: it is no longer holding two repositories in step, it is copying
   `../ui/` into the package so a wheel is self-contained. That was the one
   thing §6 got wrong — a merge does not remove the copy, only the drift.
2. ✅ **Extract the seam in filemill** — `core/ports.js` declares `FS`,
   `PREVIEW` and `ROUTER`; `core/` no longer names a data source.
   `test-ui.py` stayed at 31/31 throughout.
3. ✅ **`applyPath`/`currentPath` + hash router** — `core/deeplink.js` and
   `adapters/router-hash.js`. 12 new checks in `test-url.py`.
4. ✅ **Pykofinder JSON API** — `/api/dir`, `/api/raw`, `/api/preview`,
   `POST /api/render`, all root-relative and guarded by `_resolve_safe()`.
5. ✅ **`http.js` + path router** — the shared UI runs at `/n/`, the HTMX UI at
   `/f/` untouched. `test_browser_new_ui.py` drives it in a real browser.
6. ✅ **VFS through the adapter** — SQLite/JSON/CSV as directories with a
   `vpath`, plus the predicted `node.icon` override. It needed no change to
   `core/` at all, which is the strongest evidence the seam is in the right
   place. `/n/sample.db/users/1` deep-links to a row.
7. ⬜ **Cut over** — point `UI_BASE` at `/`, delete `columns.py` and the JS/CSS
   blob in `styles.py`, keep the PWA manifest and service worker.
8. ✅ **Rich renderers in filemill** — done as **CDN lazy-loading**, not the
   two build profiles §4b recommended. markdown-it (+ footnote, deflist,
   task-lists, anchor), highlight.js and mammoth are imported on first use, so
   the bundle stays one portable file. Behind a remembered switch, since it is
   the only thing there that touches the network, and every failure falls back
   to the raw source. `pykofinder` does not load it — Python renders better.
9. ✅ **"Open local folder…" in Pykofinder** — `app-http.js` re-points the ports
   at `FSA` + `PreviewUpload` at runtime, so the served page browses a granted
   folder with the Python renderers still doing the previews.

Two things turned out differently from the plan:

- **Mobile is untouched** and is the largest remaining unknown (§8).
- **The old UI's browser tests need a network** (htmx and mermaid come from
  CDNs) and fail offline. The shared UI fetches nothing external, which was not
  a stated goal but is worth keeping.

---

## 8 · Risks and open questions

- **Step 2 is where this succeeds or fails.** If the seam is extracted with the
  test suite green and no behaviour change, everything downstream is
  mechanical. If it drags in "while we're here" changes, it stops being a
  refactor and starts being a rewrite.
- **Perf budget must survive HTTP.** Filemill asserts ≤ 20 ms re-render and
  ≤ 25 ms keystroke at 3 000 entries. Those budgets are about DOM work and hold
  for either adapter, but arrow-key navigation that triggers a fetch per
  directory needs the `OPEN_GRACE` treatment plus a prefetch of the next
  column. Worth an explicit budget for "keystroke → column open over
  localhost".
- **Pygments ↔ highlight.js class mismatch.** Don't fight it; ship a stylesheet
  per highlighter.
- **Mobile.** Pykofinder has real mobile work (issues #42, #43, #45); the
  Miller-columns UI has none. Whether the fold dial has a touch story is an
  open design question and may be the largest unbudgeted item here.
- **PWA.** Pykofinder's manifest/SW carry over. Filemill's TASKS.md wants the
  same — shared once the repos are.
- **Bundle figures in §4b are estimates**, not measured. Measure before
  committing to the two-profile design.
- **Non-Chromium browsers.** Filemill is Chromium-only by construction (FSA).
  Pykofinder is not, and must not become so — the FSA adapter has to be
  feature-detected, not assumed.
