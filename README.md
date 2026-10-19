# Filemill

Filemill is a file explorer in Miller columns. It has two editions. Both run
the same application.

```
ui/        the shared UI — columns, folding, the trail, keyboard, deep links,
           sort order
static/    one portable index.html that browses a folder on your own machine
server/    a local web app that browses a folder on the server, in Python
```

`ui/core/model/` owns nodes, selection, sorting, folding arithmetic, keyboard
actions and deep links. Its modules run without a DOM. Nodes are plain
`{name, dir, kids}` objects. The browser renderer lives beside the model in
`ui/core/`; `dom-renderer.js` owns element handles and font measurements. `ui/adapters/` supplies the source through three
ports declared in [`ui/core/ports.js`](ui/core/ports.js):

| | **static** | **server** |
| --- | --- | --- |
| filesystem | File System Access API, including permitted saves and deletes | HTTP API for served files; FSA for Open Folder |
| Markdown / DOCX | Browser markdown-it / mammoth, pinned CDN downloads controlled by the rich-preview switch | Same browser renderers, vendored under `/ui/vendor/`, independent of the switch |
| reStructuredText | Browser Pyodide + docutils, pinned CDN download controlled by the switch | Python docutils for served files and archive members |
| PowerPoint | Browser extracts slide text locally, without a download or consent switch | Same slide-text extraction, including archive members |
| source highlighting | Shared browser `core/syntax.js` | Same browser highlighter; Python Pygments colours archive members through `/api/preview` |
| router | `#r=root&p=a/b.md` | Root-relative file path, for example `/a/b.md`; `/n/` also serves the shell |

The renderer choices are implemented in
[`app-fsa.js`](ui/adapters/app-fsa.js),
[`app-http.js`](ui/adapters/app-http.js),
[`preview-rich.js`](ui/adapters/preview-rich.js) and
[`preview.py`](server/src/filemill/preview.py). The server's
[`app.py`](server/src/filemill/app.py) maps browser dependencies to vendored
modules. PPTX previews show slide numbers and extracted paragraph text, without
slide layout, images or animations. DOCX conversion produces HTML rather than
an exact Office page layout.

Open Folder uses browser renderers for Markdown, DOCX and PPTX. Its RST
routing still incorrectly requests the server preview, which cannot read a
browser-owned file. This is the open A8 limit in the
[architecture review](docs/ARCHITECTURE-REVIEW.md).

The ports also set the cost of each edition. A sort by size needs a size per
row. The server listing has the size. The File System Access API gives names
and handles only, so the static edition calls `getFile()` one time per entry.
Each call takes about 300 µs, so 3 000 entries take about one second.
`ui/core/sort.js` is one implementation with two prices.

JSON previews remember collapsed objects during the current session. Matching
paths at the same depth stay collapsed when you browse similar objects. An
explicit expansion takes precedence for that object.

Right-click a file or folder to open its context menu. On touch screens, press
and hold the item. With the keyboard, use Shift+F10 or the Context Menu key
on the current item. Use the arrow keys to choose an action, Enter to run it,
and Escape to close the menu. Delete asks for confirmation before it removes
the item and refreshes its folder. Deleting a folder also removes its contents.

The preview toolbar has a Fullscreen button. The preview stays in fullscreen
when the browser resizes. Use Exit fullscreen or the browser fullscreen exit
control to return to the file browser.

Markdown and WebVTT previews have one Raw link and a Source/Rendered toggle
in both editions, including the server's Open Folder mode. Source shows the
original text without changing the selection. Raw opens a browser-owned file
in a new tab and a served file at its raw URL.

Rendered Markdown hides HTML comments. Source and Raw keep them. Comments
inside code stay visible. Other raw HTML stays escaped. See
[ADR 0083](docs/adr/0083-hide-markdown-comments.md).

Markdown text and code wrap on portrait phones. Wide Markdown tables scroll
inside the preview, so every column stays reachable.

One repository holds both editions. Two copies of one UI drift apart one bug
fix at a time. A fix to `ui/` is a fix to both editions in one commit.

> The server edition was called **pykofinder**. `FILEMILL_*` environment
> lookup retains `PYKOFINDER_*` fallbacks through
> [`env.py`](server/src/filemill/env.py). CLI arguments and ASGI configuration
> differ; see the [server startup table](server/README.md#usage).

## static — one file, no server, no install

```bash
cd static
python3 -m http.server 8000 -d ..     # then …
#   localhost:8000/static/index-dev.html   ← dev, no build step
./build-index.py                      #   → index.html, self-contained
#   localhost:8000/static/index.html       ← the bundle
```

`index.html` is generated and committed. It is the whole application; GitHub
Pages also gets the PWA manifest, service worker and icons beside it.
`./build-index.py --check` fails when the bundle is stale. CI publishes the
bundle to GitHub Pages. `showDirectoryPicker()` needs a secure context, so the
file opened from disk cannot open a folder. An `https://` page can.

Markdown, DOCX and reStructuredText load pinned renderer modules from a CDN
on first use when the remembered rich-preview switch is on, its default.
The switch in settings disables these downloads. Pyodide runs docutils for
RST, about 6 MB transferred and 13 MB unpacked as recorded in
[ADR 0002](docs/adr/0002-rst-in-browser.md). If loading fails, the renderer
tries a bounded text fallback and an offline note. Binary DOCX bytes may have
no readable text fallback. PPTX slide-text extraction works without the CDN.
See [`preview-rich.js`](ui/adapters/preview-rich.js) for the pins, consent
check, extraction and fallback paths.

Folder reads stay in the browser. Network access includes application loading,
renderer downloads and resources referenced by documents, such as images. The rich-preview switch is not a general network blocker.

Use the [manual FSA test checklist](static/FSA-TEST-CHECKLIST.md) for visual
checks and the headed real-folder check.

See [`static/AGENTS.md`](static/AGENTS.md).

## server — the Python edition

```bash
cd server
uv sync && uv run filemill [ROOT]
#   localhost:8000/     ← the shared UI, and "Open Folder…"
```

A directory URL with an `index.html` in it, `/` included, serves that page.
Add any query, such as `/?f`, to open the shared UI there instead.

The edition/renderer table above applies to served files and Open Folder.
JSON and JSONL navigation runs in the shared browser adapters. Python providers
browse SQLite, tar/zip archives and Git bundles, the last through `git`.
Archive member bytes reach the browser renderers for Markdown, DOCX and PPTX;
RST members use Python. See [`vfs.py`](server/src/filemill/vfs.py),
[`app-http.js`](ui/adapters/app-http.js) and
[`vfs-json.js`](ui/adapters/vfs-json.js).

Markdown source previews (`?filemill=highlight`) keep the original text and
color headings, code, URLs, and links. Links are clickable. Served relative
Markdown links open in rendered mode unless the link selects another mode.
Link queries and fragments are preserved in both preview modes.

See [`server/CONTRIBUTING.md`](server/CONTRIBUTING.md).

In JSON, JSONL, and SQLite hierarchies, select a scalar key to preview its value.
String values preserve line breaks. Objects and arrays keep their foldable previews.
JSON documents up to 8 MiB support previews and nested navigation in both editions.
Larger JSON documents show the size limit. Ordinary text previews keep the 512 KiB limit.

Markdown and reStructuredText files open as columns of their headings. Select the
file to preview it whole, or a section to preview and link to that section alone.
In the server edition, section URLs also open directly in a new tab. To open the
whole Markdown file at a heading, use `guide.md?f#heading-slug`. Fragments use
GitHub heading slugs: lowercase, with punctuation removed and spaces changed to
hyphens. For example, `Q1: scope` uses `#q1-scope`. Existing renderer fragments
such as `#q1%3A-scope` also work. An unknown heading keeps the whole file open.

## Working on the shared UI

Edit `ui/`. It is a symlink to `server/src/filemill/ui/`. A wheel cannot reach
outside its package, so the files live in the server package. There is one set
of files and nothing to keep in sync.

Restart a running server after you update UI files. The server computes asset
version URLs at startup. A browser reload without a server restart can reuse
older cached UI files.

Rebuild the static bundle after a change, as the static section above shows.
A checkout needs symlink support. Windows needs developer mode for that.

## Tests

Install and run the local quality gate as described in
[CONTRIBUTING.md](CONTRIBUTING.md#tests). It also checks that Python lint
suppressions link to focused issues.

```bash
uv run pytest                              # both editions
uv run pytest static/tests --bundle         # generated static bundle, default
uv run pytest static/tests --dev            # shared sources without a build
uv run pytest static/tests/test_ui.py       # UI and fake directory handle
uv run pytest static/tests/test_url.py      # deep links and real OPFS files
uv run pytest static/tests/test_rich.py     # offline, consent and rich renderers
(cd server && uv run pytest)                # server tests only
```

The root uv workspace uses the shared lock and the pinned Playwright release.
[`server/CONTRIBUTING.md`](server/CONTRIBUTING.md#running-tests) covers browser
setup. Each static section is a separate pytest test;
failures report its name and assertion. The fixtures provide isolated pages,
fake directory handles, an OPFS directory and a loopback HTTP server.

`static/test-e2e.py` remains a manual test with a real folder picker.

## Goals, review and roadmap

- [`docs/GOALS.md`](docs/GOALS.md) — what Filemill must become, and the
  goals the code already shows.
- [`docs/ARCHITECTURE-REVIEW.md`](docs/ARCHITECTURE-REVIEW.md) — the distance
  between the code and the goals, with file and line for each finding.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — the order in which we close the gap.

These three are not tasks, so they are in `docs/` and not in `docs/tasks/`.
`TASKS.md` issues that implement the roadmap name its phase, for example
`(roadmap Phase 0)`.

## License

MIT

## Native shell

The Linux [WebKitGTK shell](native/README.md) runs the shared DOM UI and
supplies native file, preview and history operations. Its README has the
requirements and build commands.
[ADR 0079](docs/adr/0079-native-shell.md) records why this shell was kept
and its binary size.
