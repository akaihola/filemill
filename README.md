# Filemill

Filemill is a file explorer in Miller columns, with previews and text editing.
The static and server editions share one UI. A Linux WebKitGTK prototype runs
that UI with native filesystem and history operations.

## Choose an edition

| | **static** | **server** |
| --- | --- | --- |
| filesystem | Browser File System Access API, including permitted saves and deletes | HTTP API for served files; browser access for Open Folder |
| Markdown / DOCX | Browser markdown-it / mammoth, pinned CDN downloads controlled by the rich-preview switch | Same browser renderers, vendored under `/ui/vendor/`, independent of the switch |
| reStructuredText | Browser Pyodide + docutils, controlled by the switch | Python docutils for served files and archive members |
| PowerPoint | Local slide-text extraction, without a download or consent switch | Same extraction, including archive members |
| source highlighting | Shared browser highlighter | Same highlighter, archive members included |
| structured files | JSON, JSONL, CSV and document headings | Same, plus SQLite, tar/zip archives and Git bundles |
| navigation URLs | `#r=root&p=a/b.md` | Root-relative paths, such as `/a/b.md`; Open Folder has no URL sync |

DOCX produces HTML, not exact Office page layout. PPTX shows slide numbers and
paragraph text, without slide layout, images or animations. The server's Open
Folder mode shows RST as source, and the native Source view remains limited;
see [architecture finding A8].

The [native guide] covers its prerequisites, commands and limitations. It is a
Linux prototype, without native deletion or remembered folders. Cross-platform
native feature parity remains a goal.

## static — one file, no server, no install

From a checkout, serve the repository and open
`http://localhost:8000/static/index.html`:

```bash
python3 -m http.server 8000
```

The committed bundle is one HTML file. GitHub Pages also publishes its PWA
manifest, service worker and icons. Use localhost or HTTPS and a browser with
`showDirectoryPicker()` support. Opening the bundle with `file://` shows
instructions instead of a folder picker.

Folder reads stay in the browser. Markdown, DOCX and RST download pinned
renderers on first use when the remembered rich-preview switch is on, its
default. The switch controls those downloads; application loading and images
referenced by documents can also use the network. A failed rich-renderer load
tries a bounded text fallback; binary DOCX may have no readable fallback.
The server worker's offline-copy guarantees do not apply to the static worker;
see [architecture finding A5].

## server — the Python edition

```bash
cd server
uv sync
uv run filemill .
```

Open `http://127.0.0.1:8000/?f`. The root defaults to the working directory;
the listener defaults to loopback. A bare directory URL serves its
`index.html` when present. Adding a query, such as `?f`, opens Filemill there.

See the [server startup reference] for options and environment variables,
including the `PYKOFINDER_*` compatibility names. A public instance must use
`--public` or `FILEMILL_PUBLIC=1`. Read the [security policy] before exposing
a root: direct-root symlinks are bookmarks, and bare HTML has the app's origin.

The server supplies Markdown and DOCX dependencies locally and hides the
download switch, including in Open Folder mode. Served search needs `rg`; browsing
Git bundles needs `git`. The [server recovery guide] explains offline copies,
read-only browsing during an outage and reconnecting after a restart.

Content search covers the focused folder in both served and Open Folder modes.
Browser-owned searches read granted files locally.
See the [search behavior].

## Using Filemill

The [usage guide] covers navigation, settings and their defaults, preview
modes, document headings, JSON refresh, copying and editing. The [manual
folder checklist] covers checks that need a real folder picker.

## Working on the shared UI

Edit [ui/], a symlink to [server/src/filemill/ui/]. The Python wheel packages
those files directly. The static development page loads their ES modules:

```bash
python3 -m http.server 8000
# Open http://localhost:8000/static/index-dev.html
```

After changing the shared UI, rebuild and check the committed bundle:

```bash
static/build-index.py
static/build-index.py --check
```

Restart a running server after UI changes. It computes asset version URLs at
startup, so reloading only the browser can reuse older assets. A checkout
needs symlink support; Windows needs a configuration that permits symlinks.

[ui/core/model/] owns DOM-free selection, sorting, folding, keys and deep
links. Adjacent browser modules render them. The [adapter guide] explains
filesystem, preview and router wiring; [ui/core/ports.js] defines the contract.

## Tests

Use the [contributor guide] for setup, browser prerequisites, test commands and
the local quality gate. Root pytest collects the server and static browser
editions; native checks and the interactive picker check have separate commands.
The [testing index] distinguishes current checks from historical results.

## Goals, review and roadmap

- [Goals] describe the target and the capabilities already present.
- [Architecture review] records remaining implementation gaps.
- [Roadmap] groups delivered and remaining work by phase.
- [Documentation review] records this audit's evidence and open decisions.
- [Tracker] records work status and user acceptance separately.

## License

MIT; see [LICENSE].

[architecture finding A5]: docs/ARCHITECTURE-REVIEW.md#a5-the-static-service-worker-retains-the-old-policy
[architecture finding A8]: docs/ARCHITECTURE-REVIEW.md#a8-preview-source-and-representation-are-conflated
[native guide]: native/README.md
[server startup reference]: server/README.md#usage
[security policy]: SECURITY.md
[server recovery guide]: server/README.md#installed-pwa
[usage guide]: docs/USAGE.md
[manual folder checklist]: static/FSA-TEST-CHECKLIST.md
[ui/]: ui/
[server/src/filemill/ui/]: server/src/filemill/ui/
[ui/core/model/]: ui/core/model/
[adapter guide]: server/src/filemill/ui/adapters/README.md
[ui/core/ports.js]: ui/core/ports.js
[contributor guide]: CONTRIBUTING.md
[testing index]: docs/testing/README.md
[Goals]: docs/GOALS.md
[Architecture review]: docs/ARCHITECTURE-REVIEW.md
[Roadmap]: docs/ROADMAP.md
[Documentation review]: docs/reviews/2026-10-22-docs-review.md
[Tracker]: TASKS.md
[LICENSE]: LICENSE

[search behavior]: docs/USAGE.md#content-search
