# filemill + pykofinder

Two file explorers with one frontend.

```
ui/           the shared Miller-columns UI — the thing both projects are
filemill/     a single portable index.html that browses a folder on your machine
pykofinder/   a local web app that browses a folder on the server, in Python
```

`ui/core/` is the application: columns, the fold dial, the trail, the keyboard
model, the preview pane, deep links. It knows about *nodes* and nothing about
where a node comes from. `ui/adapters/` is what fills that in, through three
small ports declared in [`ui/core/ports.js`](ui/core/ports.js):

| | filemill | pykofinder |
| --- | --- | --- |
| filesystem | File System Access API | `GET /api/dir` |
| preview | markdown-it / highlight.js, fetched on demand | `GET /api/preview` — Python renderers |
| router | `#r=root&p=a/b.md` | `/n/a/b.md` — the path *is* the file path |

They are one repository because the alternative was two, and two lookalike UIs
drift apart one bug fix at a time no matter how much discipline is applied to
copying between them. Here a fix to `ui/` is a fix to both, in one commit.

## filemill

```bash
cd filemill
python3 -m http.server 8000 -d ..     # then …
#   localhost:8000/filemill/index-dev.html   ← dev, no build step
./build-index.py                      #   → index.html, one self-contained file
#   localhost:8000/filemill/index.html       ← the bundle
```

`index.html` is generated *and* committed: one file is the whole deliverable.
`./build-index.py --check` fails when it has gone stale, and CI publishes it to
GitHub Pages — which matters because `showDirectoryPicker()` needs a secure
context, so the same file opened from disk cannot open a folder at all.

See [`filemill/AGENTS.md`](filemill/AGENTS.md).

## pykofinder

```bash
cd pykofinder
uv sync && uv run pykofinder [ROOT]
#   localhost:8000/f/    ← the HTMX UI (current default)
#   localhost:8000/n/    ← the shared UI, and "Open local folder…"
```

Rich previews — Markdown with plugins, Pygments, docx, pptx, SQLite/JSON
virtual filesystems — are rendered in Python and served into the shared preview
pane, which is why none of that had to be rewritten in JavaScript. Opening a
*local* folder from the served page still uses them: the bytes are posted to
`/api/render`.

See [`pykofinder/CONTRIBUTING.md`](pykofinder/CONTRIBUTING.md).

## Working on the shared UI

Edit `ui/`. Never edit `pykofinder/src/pykofinder/ui/` — that is a copy made by
`pykofinder/tools/sync-ui.py` so that a wheel carries what it needs at runtime,
and `--check` fails when it is stale.

```bash
cd filemill    && ./build-index.py                    # rebuild the bundle
cd pykofinder  && ./tools/sync-ui.py                  # refresh the packaged copy
```

## Tests

```bash
cd filemill
uv run --with "playwright==1.61.0" python3 test-ui.py     # UI, fake handle
uv run --with "playwright==1.61.0" python3 test-url.py    # deep links
uv run --with "playwright==1.61.0" python3 test-rich.py   # CDN renderers
#   each also takes --dev, to run against ui/ unbundled

cd pykofinder && uv run pytest
```

## License

MIT
