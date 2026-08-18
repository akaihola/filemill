# Filemill

A file explorer in Miller columns, in two editions that are the same
application.

```
ui/        the shared UI — columns, folding, the trail, keyboard, deep links
static/    one portable index.html that browses a folder on your own machine
server/    a local web app that browses a folder on the server, in Python
```

`ui/core/` *is* the application. It knows about **nodes** — `{name, dir, kids}`
— and nothing about where a node comes from. `ui/adapters/` supplies that,
through three small ports declared in [`ui/core/ports.js`](ui/core/ports.js):

| | **static** | **server** |
| --- | --- | --- |
| filesystem | File System Access API | `GET /api/dir` |
| preview | markdown-it / highlight.js, fetched on demand | `GET /api/preview` — Python renderers |
| router | `#r=root&p=a/b.md` | `/n/a/b.md` — the path *is* the file path |

One repository because the alternative was two, and two lookalike UIs drift
apart one bug fix at a time however much discipline is applied to copying
between them. Here a fix to `ui/` is a fix to both, in one commit.

> The server edition was called **pykofinder** until it was folded in here.
> `FILEMILL_ROOT` and friends are the current environment variables; the
> `PYKOFINDER_*` names still work, so existing setups keep running.

## static — one file, no server, no install

```bash
cd static
python3 -m http.server 8000 -d ..     # then …
#   localhost:8000/static/index-dev.html   ← dev, no build step
./build-index.py                      #   → index.html, self-contained
#   localhost:8000/static/index.html       ← the bundle
```

`index.html` is generated *and* committed — one file is the whole deliverable.
`./build-index.py --check` fails when it has gone stale, and CI publishes it to
GitHub Pages. That last part matters more than it sounds: `showDirectoryPicker()`
needs a secure context, so the same file opened from disk cannot open a folder
at all. An `https://` link can.

Rich previews (Markdown, syntax highlighting, .docx) are fetched from a CDN on
first use rather than bundled, behind a switch in ⚙ — it is the only thing here
that touches the network. Offline, previews fall back to the raw source.

See [`static/AGENTS.md`](static/AGENTS.md).

## server — the Python edition

```bash
cd server
uv sync && uv run filemill [ROOT]
#   localhost:8000/f/    ← the older HTMX UI (still the default)
#   localhost:8000/n/    ← the shared UI, and "Open local folder…"
```

Markdown with plugins, Pygments, docx, pptx, and SQLite/JSON virtual
filesystems are all rendered in Python and served into the shared preview pane
— which is why none of it had to be rewritten in JavaScript. Opening a *local*
folder from the served page still uses them: the bytes are posted to
`/api/render`.

See [`server/CONTRIBUTING.md`](server/CONTRIBUTING.md).

## Working on the shared UI

Edit `ui/`. Never edit `server/src/filemill/ui/` — that is a copy made by
`server/tools/sync-ui.py` so a wheel carries what it needs at runtime, and
`--check` fails when it is stale.

```bash
(cd static && ./build-index.py)      # rebuild the bundle
(cd server && ./tools/sync-ui.py)    # refresh the packaged copy
```

## Tests

```bash
cd static
uv run --with "playwright==1.61.0" python3 test-ui.py     # UI, fake handle
uv run --with "playwright==1.61.0" python3 test-url.py    # deep links
uv run --with "playwright==1.61.0" python3 test-rich.py   # CDN renderers
#   each also takes --dev, to run against ui/ unbundled

cd server && uv run pytest
```

## License

MIT
