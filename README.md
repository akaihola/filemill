# Filemill

Filemill is a file explorer in Miller columns. It has two editions. Both run
the same application.

```
ui/        the shared UI — columns, folding, the trail, keyboard, deep links,
           sort order
static/    one portable index.html that browses a folder on your own machine
server/    a local web app that browses a folder on the server, in Python
```

`ui/core/` is the application. It knows **nodes** — `{name, dir, kids}` — and
nothing about their source. `ui/adapters/` supplies the source through three
ports declared in [`ui/core/ports.js`](ui/core/ports.js):

| | **static** | **server** |
| --- | --- | --- |
| filesystem | File System Access API | `GET /api/dir` |
| preview | markdown-it / highlight.js, fetched on demand | `GET /api/preview` — Python renderers |
| router | `#r=root&p=a/b.md` | `/n/a/b.md` — the path *is* the file path |

The ports also set the cost of each edition. A sort by size needs a size per
row. The server listing has the size. The File System Access API gives names
and handles only, so the static edition calls `getFile()` one time per entry.
Each call takes about 300 µs, so 3 000 entries take about one second.
`ui/core/sort.js` is one implementation with two prices.

One repository holds both editions. Two copies of one UI drift apart one bug
fix at a time. A fix to `ui/` is a fix to both editions in one commit.

> The server edition was called **pykofinder**. `FILEMILL_ROOT` and the other
> `FILEMILL_*` variables are current. The `PYKOFINDER_*` names still work.

## static — one file, no server, no install

```bash
cd static
python3 -m http.server 8000 -d ..     # then …
#   localhost:8000/static/index-dev.html   ← dev, no build step
./build-index.py                      #   → index.html, self-contained
#   localhost:8000/static/index.html       ← the bundle
```

`index.html` is generated and committed. It is the whole deliverable.
`./build-index.py --check` fails when the bundle is stale. CI publishes the
bundle to GitHub Pages. `showDirectoryPicker()` needs a secure context, so the
file opened from disk cannot open a folder. An `https://` page can.

Rich previews (Markdown, .docx, reStructuredText, .pptx) load from a CDN on
first use. A switch in ⚙ turns them off. This is the only network access.
reStructuredText runs docutils on Pyodide, a 13 MB one-time download.
PowerPoint files open in `pptx-vanilla-viewer`, a 4 MB one-time download.
Offline, the preview shows the raw source, or says that the viewer is
unavailable for a `.pptx` file. Every CDN URL carries a version pin; see
[ADR 0040](docs/adr/0040-version-pins-on-every-cdn-url.md).

See [`static/AGENTS.md`](static/AGENTS.md).

## server — the Python edition

```bash
cd server
uv sync && uv run filemill [ROOT]
#   localhost:8000/     ← the shared UI, and "Open local folder…"
```

Python renders Markdown with plugins, Pygments, docx and the JSON virtual
filesystem. The result goes into the shared preview pane. SQLite rows arrive as
JSON and the shared JSON view draws them. A local
folder opened from the served page posts its bytes to `/api/render`, so the
same renderers apply. PowerPoint files are the one exception: both editions
open them in the browser with `pptx-vanilla-viewer` from the CDN.

See [`server/CONTRIBUTING.md`](server/CONTRIBUTING.md).

## Working on the shared UI

Edit `ui/`. It is a symlink to `server/src/filemill/ui/`. A wheel cannot reach
outside its package, so the files live in the server package. There is one set
of files and nothing to keep in sync.

```bash
(cd static && ./build-index.py)      # rebuild the bundle
```

The bundle is generated and committed, so it can go stale. CI runs
`./build-index.py --check`. A checkout needs symlink support. Windows needs
developer mode for that.

## Tests

```bash
cd static
uv run --with "playwright==1.61.0" python3 test-ui.py     # UI, fake handle
uv run --with "playwright==1.61.0" python3 test-url.py    # deep links
uv run --with "playwright==1.61.0" python3 test-rich.py   # CDN renderers
#   each also takes --dev, to run against ui/ unbundled

cd server && uv run pytest
```

## Goals, review and roadmap

- [`docs/GOALS.md`](docs/GOALS.md) — what Filemill must become, and the
  goals the code already shows.
- [`docs/ARCHITECTURE-REVIEW.md`](docs/ARCHITECTURE-REVIEW.md) — the distance
  between the code and the goals, with file and line for each finding.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — the order in which we close the gap.

These three are not tasks, so they are in `docs/` and not in `docs/tasks/`.
`TASKS.md` links the roadmap as one backlog item.

## License

MIT
