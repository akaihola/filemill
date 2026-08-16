# Adapters — how one UI serves two apps

`../core/` is the Miller-columns app: columns, folding, the trail, the keyboard
model, the preview pane, deep links. It knows about **nodes**, and nothing about
where a node comes from. Everything source-specific lives here, behind the three
ports declared in [`../core/ports.js`](../core/ports.js).

Both projects in this repository load these files from here — `filemill/` inlines
them into its single-file bundle, `pykofinder/` copies them into its package for
distribution. Neither has its own version to drift.

Pick a different set of adapters and the same UI browses something else. That is
the whole mechanism — there is no framework under it.

| | `filemill` (static HTML) | `pykofinder` (server) |
| --- | --- | --- |
| filesystem | `fsa.js` — File System Access API | `http.js` — `GET /api/dir` |
| preview | `preview-local.js` — text, images, PDF, `.desktop` | `preview-http.js` — `GET /api/preview`, rendered by Python |
| router | `router-hash.js` — `#r=root&p=a/b.md` | `router-path.js` — `/a/b.md` |
| boot | `app-fsa.js` — picker + welcome screen | `app-http.js` — root comes from the server |
| extra | `preview-rich.js` — renderers fetched from a CDN | `preview-upload.js` — local bytes, Python renderer |
| | `storage.js` — remembered roots in IndexedDB | |

## The ports

**`FS`** — `node(name, …)`, `ensureLoaded(node)`, `loadMeta(node)`, `blob(node)`.
A node is `{ name, dir, kids }`; `kids === null` means "not read yet" and is what
puts a spinner in the column. Nothing else is required, which is why a SQLite
table or a JSON document can be a directory as far as the UI is concerned.

**`PREVIEW`** — `render(node) → Promise<string|null>`, plus an optional
`revoke()`. Returns the HTML for the preview *body* only; the pane's header,
hero and size/modified list are core's, and so is the staleness guard, so a
provider may take as long as it needs.

**`ROUTER`** — `read()`, `write(state, replace)`, `onNavigate(cb)`, or `null` for
no URL syncing at all. The mapping between a path and the column chain is
core's ([`../core/deeplink.js`](../core/deeplink.js)) and is shared verbatim;
only the transport differs.

## Why the renderers are not ported

`preview-http.js` is the reason `preview.py`, `rendering.py`, `vfs.py` and
`providers/` never had to be rewritten in JavaScript: markdown-it-py with its
plugins, Pygments, mammoth and python-pptx keep running where they already run,
and their HTML lands in the same pane.

`preview-upload.js` closes the last gap. When the *server* build opens a local
folder, the server cannot read it — so the bytes are posted to `/api/render` and
come back rendered by the same Python pipeline. Local-folder mode is therefore
not a downgrade; only the address bar goes quiet, because a URL path names a
file under the server's root and a granted folder is not under it.

## Rich rendering in the static build

`preview-rich.js` is a *different provider*, not a bigger `preview-local.js`. It
imports markdown-it, highlight.js and mammoth from a CDN the first time a file
needs one, because bundling them would make the portable file eight times
bigger. It sits behind a remembered switch — the app's pitch is that your folder
does not leave the browser, and this is the one thing that talks to the network
at all — and every failure falls back to `preview-local.js`, so offline costs
fidelity rather than the pane.

`pykofinder` does not load it: its previews come from Python, including for a
local folder (`preview-upload.js`), which is strictly better.
