# Filemill — server edition

Filemill is a column-view file browser and previewer. The server edition is a
local web application in Python. Click a column entry to open a directory.
Previews for Markdown, DOCX, PPTX, PDF, images, plain text and source code show
inline.

The [repository README](../README.md) describes the two editions and their
shared ports. This document covers the Python edition.

## Features

- **Column view** – multi-pane navigation in the style of macOS Finder
- **Rich previews** – Markdown (with plugins), DOCX, PPTX, PDF, images, plain text, and source code with Pygments highlighting ("friendly" theme)
- **Markdown extras** – wikilinks (`[[PageName]]`), Mermaid diagrams, plain-URL links, relative-link normalisation
- **Virtual filesystem** – a SQLite database opens as table → row columns; JSON files open through their own provider
- **Static web server** – `/w/<mount>/<path>` serves a file under a named mount with the correct Content-Type. The root directory is mounted as `/w/<ROOT.name>/...`. Each direct symlink child of ROOT is mounted under its own name
- **Finder URLs** – the URL path is the file path relative to the root, for example `/docs/readme.md`. A deep link opens any location. `/sample.db/users/1` opens one database row
- **Dotfiles** – add `?hidden=show` to the URL to show them
- **Keyboard navigation** – `↑↓` move in a column; `→`/`Enter` open; `←` goes back; `Home`/`End`/`PgUp`/`PgDn` scroll
- **Live reload** – the `--live` flag restarts the server on code changes
- **`.desktop` files** – show as a link card
- **Symlink support** – follows a symlink when its target stays inside the root
- **Open local folder…** – the served page can browse a folder on your machine through the File System Access API. Python still renders the previews, because the page posts the bytes to `/api/render`
- **PWA** – installable. Includes a Web App Manifest, a service worker and an icon set. The worker caches the app shell (stale-while-revalidate) and never caches `/api/` responses

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

The default listener is `127.0.0.1:8000`, so only this machine can reach it.
The PWA cannot start a native process. When the service is stopped, the app
shows the command above and a retry button. Use `--bind` only when you want to
expose the server beyond loopback.

## Development

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the development rules.

Quick start:

```bash
uv sync
timeout 1800 uv run pytest         # everything, browser tests included

# Only the real-browser tests. Needs PLAYWRIGHT_BROWSERS_PATH. The browser
# suite takes minutes on a 4-core host, so budget accordingly.
timeout 1800 uv run pytest tests/test_browser_keyboard.py tests/test_browser_new_ui.py
```

Do not add `--with`. `uv sync` installs the Playwright version that the lock
pins. That version matches the browsers that Nix provides.
`uv run --with "playwright==1.57.0"` overrides the lock and fails like this:

```
BrowserType.launch: Executable doesn't exist at
  .../chromium_headless_shell-1200/chrome-headless-shell-linux64/chrome-headless-shell
```

The message tells you to run `playwright install`. Do not run it. Nix ships
the browsers, one revision per bundle, and `pyproject.toml` pins the Playwright
that matches them.

## Architecture

```
src/filemill/
├── app.py          # FastHTML app, routes, _resolve_safe()
├── api.py          # /api/dir, /api/search, /api/raw, /api/preview, /api/render
├── cli.py          # Typer CLI entry point
├── env.py          # FILEMILL_* variables, PYKOFINDER_* fallback
├── preview.py      # Preview dispatcher (md / docx / pptx / pdf / img / code / raw)
├── rendering.py    # markdown-it-py instance with plugins
├── styles.py       # Pygments and app CSS
├── urls.py         # View state and canonical URLs
├── vfs.py          # Virtual-filesystem registry + provider protocol
├── providers/      # VFS backends: SQLite, JSON, VTT
├── static/         # Bundled PWA assets: manifest.json, sw.js, icons/
└── ui/             # The shared frontend; the repo root's ui/ symlinks here
```

The server serves the shared Miller-columns UI at `/` and at `/n/`. The UI
source is `src/filemill/ui/`. The repository root's [`../ui/`](../ui) is a
symlink to it. There is one set of files and no packaging copy. Read
[CONTRIBUTING.md](CONTRIBUTING.md).

> The package was **pykofinder**. `PYKOFINDER_ROOT`, `PYKOFINDER_BIND` and
> `PYKOFINDER_LIVE` still work, so an existing setup keeps running.

## License

MIT
