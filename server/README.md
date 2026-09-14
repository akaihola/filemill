# Filemill — server edition

A column-view file browser and previewer, served as a local web application.
Navigate directories by clicking column entries; previews render inline for
Markdown, DOCX, PPTX, PDF, images, plain text, and source code.

The two editions and their shared ports are described in the
[repository README](../README.md). This document covers the Python edition.

## Features

- **Column view** – multi-pane navigation à la macOS Finder
- **Rich previews** – Markdown (with plugins), DOCX, PPTX, PDF, images, plain text, source code with syntax highlighting (Pygments "friendly" theme)
- **Markdown extras** – wikilinks (`[[PageName]]`), Mermaid diagrams, plain-URL linkification, relative-link normalisation
- **Virtual filesystem** – SQLite databases are browsable as navigable table → row columns; additional VFS providers for JSON and CSV files
- **Static web server** – `/w/<mount>/<path>` serves any file under a named mount with the correct Content-Type (useful for HTML files); the root directory itself is mounted as `/w/<ROOT.name>/...`, and each direct symlink child of ROOT is mounted under its own name
- **Canonical finder URLs** – workspace-local navigation uses `/n/<path>` in the shared UI; legacy `/f/<mount>/<path>` and `/f/?path=<absolute>` remain accepted for compatibility fallbacks
- **Breadcrumb trail** – `~ / dir / subdir / file` navigation bar; includes a `.*` dotfile toggle that persists across sessions
- **URL sync** – browser URL stays in sync with the selected path using `/n/<path>` URLs in the shared UI; deep-link any location directly
- **Keyboard navigation** – `↑↓` move within a column; `→`/`Enter` open; `←` go back while keeping the URL in sync with the visible parent/root state; `Home`/`End`/`PgUp`/`PgDn` scroll; column focus states visually indicated
- **Live reload** – `--live` flag restarts the server on code changes
- **Zoom** – expand preview pane to full viewport width
- **`.desktop` hyperlinks** – open service URLs directly from the browser
- **Symlink support** – safely follows symlink bookmarks in the configured root
- **Miller-columns UI (new, at `/n/`)** – the shared frontend from
  [`../ui/`](../ui): column headers with counts, three selection states, a
  drawn trail between selected rows, and horizontal scroll as a fold dial. Its
  URL path mirrors the file path relative to the browsed root exactly
  (`/n/docs/readme.md`), and previews still come from the Python renderers below.
  SQLite/JSON virtual filesystems browse through it too — `/n/sample.db/users/1`
  deep-links to a single row
- **Open local folder…** – the same page can browse a folder on *your* machine
  through the File System Access API instead of the served root; previews are
  still rendered by markdown-it-py, Pygments and mammoth, because the bytes are
  posted to `/api/render`
- **PWA** – installable as a Progressive Web App; includes a Web App Manifest, service worker (stale-while-revalidate for the app shell, network-only for API and dynamic responses), and full icon set

## Installation

```bash
uv sync
```

## Usage

```bash
uv run filemill [OPTIONS] [ROOT]
```

| Option          | Default   | Env var             | Description                      |
| --------------- | --------- | ------------------- | -------------------------------- |
| `ROOT`          | `$PWD`    | `FILEMILL_ROOT`   | Root directory to browse         |
| `--port`        | `8000`    | –                   | TCP port to listen on            |
| `--bind` / `-b` | `127.0.0.1` | `FILEMILL_BIND` | Network interface to bind to |
| `--live`        | off       | `FILEMILL_LIVE=1` | Enable auto-reload (development) |

## Installed PWA

The installed app connects to the Filemill server on its own origin. Start the
local service first:

```bash
uv run filemill [ROOT]
```

The default listener is `127.0.0.1:8000`, so it is local to this machine. The
PWA cannot start a native process; if the service is stopped, it shows the same
command and a retry button. Use `--bind` only when deliberately exposing the
server beyond loopback.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development workflow and rules.

Quick start:

```bash
uv sync
timeout 1800 uv run pytest         # everything, browser tests included

# Just the 76 real-browser tests. Needs PLAYWRIGHT_BROWSERS_PATH. The browser
# suite takes minutes on a 4-core host, so budget accordingly.
timeout 1800 uv run pytest tests/test_browser_keyboard.py tests/test_browser_new_ui.py
```

Note the absence of `--with`. `uv sync` installs the Playwright the lock pins,
and that version is the one whose driver matches the browsers Nix provides.
`uv run --with "playwright==1.57.0"` overrides the lock and fails like this:

```
BrowserType.launch: Executable doesn't exist at
  .../chromium_headless_shell-1200/chrome-headless-shell-linux64/chrome-headless-shell
```

The message ends by telling you to run `playwright install`. Do not. Nix already
ships the browsers, one revision per bundle, and `pyproject.toml` pins the
Playwright that matches them.

The legacy `/f/` tests in `tests/test_browser_keyboard.py` need outbound network:
that compatibility shell loads htmx from `unpkg.com` and mermaid from
`cdn.jsdelivr.net`.
They read `$HTTPS_PROXY` and hand Chromium its credentials, because Chromium
reads that variable but drops the username and password in it. Without a route
to those two hosts the page still draws its first column and then ignores every
click, which reads like a navigation bug and is not one. The 27 tests in
`tests/test_browser_new_ui.py` serve every asset themselves and pass offline.

## Architecture

```
src/filemill/
├── app.py          # FastHTML app, routes, _resolve_safe()
├── api.py          # /api/dir, /api/raw, /api/preview, /api/render
├── cli.py          # Typer CLI entry point
├── columns.py      # Legacy /f/ column HTML generation
├── preview.py      # Preview dispatcher (md / docx / pptx / pdf / img / code / raw)
├── rendering.py    # markdown-it-py instance with plugins
├── styles.py       # Legacy /f/ CSS and scripts
├── vfs.py          # Virtual-filesystem registry + provider protocol
├── providers/      # VFS backends: SQLite, JSON, CSV
├── static/         # Bundled PWA assets: manifest.json, sw.js, icons/
└── ui/             # The shared frontend; the repo root's ui/ symlinks here
```

The shared Miller-columns UI is served at `/n/`. The legacy HTMX UI remains at
`/f/` for compatibility. The shared UI source is
`src/filemill/ui/`, which the repository root's [`../ui/`](../ui) symlinks to.
There is one set of files and no packaging copy; see [CONTRIBUTING.md](CONTRIBUTING.md).

> Renamed from **pykofinder**. `PYKOFINDER_ROOT`, `PYKOFINDER_BIND` and
> `PYKOFINDER_LIVE` are still honoured, so an existing setup keeps running.

## License

MIT
