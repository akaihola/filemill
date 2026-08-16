# pykofinder

A macOS Finder-style column-view file browser and previewer, served as a local
web application. Navigate directories by clicking column entries; previews render
inline for Markdown, DOCX, PPTX, PDF, images, plain text, and source code.

## Features

- **Column view** – multi-pane navigation à la macOS Finder
- **Rich previews** – Markdown (with plugins), DOCX, PPTX, PDF, images, plain text, source code with syntax highlighting (Pygments "friendly" theme)
- **Markdown extras** – wikilinks (`[[PageName]]`), Mermaid diagrams, plain-URL linkification, relative-link normalisation
- **Virtual filesystem** – SQLite databases are browsable as navigable table → row columns; additional VFS providers for JSON and CSV files
- **Static web server** – `/w/<mount>/<path>` serves any file under a named mount with the correct Content-Type (useful for HTML files); the root directory itself is mounted as `/w/<ROOT.name>/...`, and each direct symlink child of ROOT is mounted under its own name
- **Canonical finder URLs** – workspace-local navigation uses `/f/<mount>/<path>` in the address bar; legacy `/f/?path=<absolute>` remains accepted for compatibility fallbacks
- **Breadcrumb trail** – `~ / dir / subdir / file` navigation bar; includes a `.*` dotfile toggle that persists across sessions
- **URL sync** – browser URL stays in sync with the selected path using canonical `/f/<mount>/<path>` URLs for workspace-local files; deep-link any location directly
- **Keyboard navigation** – `↑↓` move within a column; `→`/`Enter` open; `←` go back while keeping the URL in sync with the visible parent/root state; `Home`/`End`/`PgUp`/`PgDn` scroll; column focus states visually indicated
- **Live reload** – `--live` flag restarts the server on code changes and refreshes the browser on content changes via SSE
- **Zoom** – expand preview pane to full viewport width
- **`.desktop` hyperlinks** – open service URLs directly from the browser
- **Symlink support** – safely follows symlink bookmarks in the configured root
- **Miller-columns UI (new, at `/n/`)** – the frontend shared verbatim with
  [filemill](../filemill): column headers with counts, three selection states, a
  drawn trail between selected rows, and horizontal scroll as a fold dial. Its
  URL path mirrors the file path relative to the browsed root exactly
  (`/n/docs/readme.md`), and previews still come from the Python renderers below.
  SQLite/JSON virtual filesystems browse through it too — `/n/sample.db/users/1`
  deep-links to a single row
- **Open local folder…** – the same page can browse a folder on *your* machine
  through the File System Access API instead of the served root; previews are
  still rendered by markdown-it-py, Pygments and mammoth, because the bytes are
  posted to `/api/render`
- **PWA** – installable as a Progressive Web App; includes a Web App Manifest, service worker (stale-while-revalidate for the app shell, network-only for dynamic partials), and full icon set

## Installation

```bash
uv sync
```

## Usage

```bash
uv run pykofinder [OPTIONS] [ROOT]
```

| Option          | Default   | Env var             | Description                      |
| --------------- | --------- | ------------------- | -------------------------------- |
| `ROOT`          | `$PWD`    | `PYKOFINDER_ROOT`   | Root directory to browse         |
| `--port`        | `8000`    | –                   | TCP port to listen on            |
| `--bind` / `-b` | `0.0.0.0` | `PYKOFINDER_BIND`   | Network interface to bind to     |
| `--live`        | off       | `PYKOFINDER_LIVE=1` | Enable auto-reload (development) |

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development workflow and rules.

Quick start:

```bash
uv sync
timeout 120 uv run pytest          # unit + integration tests with coverage

# Real-browser regression tests (requires PLAYWRIGHT_BROWSERS_PATH)
# Covers ArrowLeft URL sync and the keyboard-only parent-column survival regression.
timeout 120 PLAYWRIGHT_BROWSERS_PATH="$PLAYWRIGHT_BROWSERS_PATH" \
  uv run --with "playwright==1.57.0" pytest tests/test_browser_keyboard.py
```

## Architecture

```
src/pykofinder/
├── app.py          # FastHTML app, routes, _resolve_safe()
├── api.py          # /api/dir, /api/raw, /api/preview, /api/render
├── cli.py          # Typer CLI entry point
├── columns.py      # Column HTML generation + breadcrumb + pruning JS  (/f/ UI)
├── preview.py      # Preview dispatcher (md / docx / pptx / pdf / img / code / raw)
├── rendering.py    # markdown-it-py instance with plugins
├── styles.py       # CSS + Pygments theme + HTMX + keyboard + live-reload JS
├── vfs.py          # Virtual-filesystem registry + provider protocol
├── providers/      # VFS backends: SQLite, JSON, CSV
├── static/         # Bundled PWA assets: manifest.json, sw.js, icons/
└── ui/             # Vendored copy of filemill's frontend — do not edit
```

Two user interfaces are served side by side during the migration: the HTMX one
at `/f/` (the default) and the shared Miller-columns one at `/n/`. Only the
adapters differ between `/n/` and filemill — `ui/src/core/` is byte-identical in
both, which is what keeps the two applications from drifting apart. Re-vendor it
with `tools/sync-ui.py`; see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
