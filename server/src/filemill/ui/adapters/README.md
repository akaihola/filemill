# Adapters — how one UI serves two apps

`../core/` is the Miller-columns app: columns, folding, the trail, the keyboard
model, the preview pane, deep links. It knows **nodes** and nothing about their
source. Everything source-specific is here, behind the three ports declared in
[`../core/ports.js`](../core/ports.js).

Both editions load these files from here, through one entry module each:
`../entry-static.js` and `../entry-server.js`. Each entry names the adapters of
its edition and the app module that wires them. `static/` inlines the import
graph into its single-file bundle. `server/` serves the modules from its
package, which is where this directory is. The repository root's `ui/` is a
symlink to it. Neither edition has its own version to drift.

Pick a different set of adapters and the same UI browses something else. That is
the whole mechanism. There is no framework under it.

|            | **static** (one HTML file)                         | **server** (Python)                                        |
| ---------- | -------------------------------------------------- | ---------------------------------------------------------- |
| filesystem | `fsa.js` — File System Access API                  | `http.js` — `GET /api/dir`                                 |
| preview    | `preview-local.js` — text, images, PDF, `.desktop` | `preview-http.js` — `GET /api/preview`, rendered by Python |
| router     | `router-hash.js` — `#r=root&p=a/b.md`              | `router-path.js` — `/a/b.md`                               |
| boot       | `app-fsa.js` — picker + welcome screen             | `app-http.js` — root comes from the server                 |
| extra      | `preview-rich.js` — renderers fetched from a CDN   | `preview-upload.js` — local bytes, Python renderer         |
|            | `storage.js` — remembered roots in IndexedDB       |                                                            |

## The ports

**`FS`** — `node(name, …)`, `ensureLoaded(node)`, `loadMeta(node)`,
`blob(node)`. A node is `{ name, dir, kids }`. `kids === null` means "not read
yet" and puts a spinner in the column. Nothing else is required. That is why a
SQLite table or a JSON document can be a directory for the UI.

Directory adapters own entry order. The contract is directories first, then
case-insensitive names, with the adapter's tie-breaker. An adapter sets
`ordered` when its loaded children follow that order; shared sorting preserves
that order. The HTTP adapter applies it on the server, and the File System
Access adapter applies equivalent browser collation while loading.

**`PREVIEW`** — `render(node) → Promise<string|null>`, plus an optional
`revoke()`. It returns the HTML for the preview _body_ only. The pane's header,
hero and size/modified list belong to core, and so does the staleness guard. A
provider can take as long as it needs.

**`ROUTER`** — `read()`, `write(state, replace)`, `onNavigate(cb)`, or `null`
for no URL sync. Core owns the mapping between a path and the column chain
([`../core/deeplink.js`](../core/deeplink.js)). Both editions share it. Only the
transport differs.

## Why the renderers are not ported

`preview-http.js` is the reason `preview.py`, `rendering.py`, `vfs.py` and
`providers/` have no JavaScript port. markdown-it-py with its plugins, Pygments,
mammoth and python-pptx keep running where they run, and their HTML lands in the
same pane.

`preview-upload.js` closes the last gap. When the _server_ edition opens a local
folder, the server cannot read it. The page posts the bytes to `/api/render`,
and the same Python pipeline renders them. Local-folder mode is therefore not a
downgrade. Only the address bar goes quiet, because a URL path names a file
under the server's root, and a granted folder is not under it.

## Rich rendering in the static build

`preview-rich.js` is a _different provider_, not a bigger `preview-local.js`. It
imports markdown-it, mammoth, or Pyodide with docutils for reStructuredText from
a CDN the first time a file needs one. A bundle with them would be eight times
bigger, or sixty times with the Python runtime. A remembered switch controls it,
because the app's promise is that your folder does not leave the browser, and
this is the one thing that talks to the network. Every failure falls back to
`preview-local.js`, so offline costs fidelity, not the pane.

## Syntax highlighting is neither of those

Both editions colour source files and fenced code the same way, in
`core/syntax.js`: no download, no switch, no Python. Every provider reaches it.
`preview-local.js` colours the text it escapes. `app-http.js` wraps the
server-side provider in use, so a file with a known language is read through
`FS.blob` and highlighted here. `hlFences` colours the
`<pre><code class="language-x">` blocks that every Markdown renderer emits,
after `fillPreview` puts them in the pane. The server keeps everything else it
renders better: Markdown, `.docx`, database rows. A virtual path is never
diverted, because only the server can read one.
