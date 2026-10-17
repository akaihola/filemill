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
- **Virtual filesystem** – a SQLite database opens as table → row columns; JSON files open through their own provider; a tar (`.tar`, `.tar.gz`, `.tar.bz2`, `.tar.xz`, `.tar.zst`) or zip archive opens as columns of its members, and a member previews as the file it is; a Git `.bundle` opens as columns of its refs (`heads/main`, `tags/v1`, `HEAD`) and then its trees, when `git` is installed
- **Static web server** – `/w/<mount>/<path>` serves a file under a named mount with the correct Content-Type. The root directory is mounted as `/w/<ROOT.name>/...`. Each direct symlink child of ROOT is mounted under its own name
- **Finder URLs** – the URL path is the file path relative to the root, for example `/docs/readme.md`. A deep link opens any location. `/sample.db/users/1` opens one database row
- **Dotfiles** – add `?hidden=show` to the URL to show them
- **Keyboard navigation** – `↑↓` move in a column; `→`/`Enter` open; `←` goes back; `Home`/`End`/`PgUp`/`PgDn` scroll
- **Live reload** – the `--live` flag restarts the server on code changes
- **`.desktop` files** – show as a link card
- **Symlink bookmarks** – a direct symlink child of the root opens as a bookmark, and its target subtree is browsable
- **Open local folder…** – the served page can browse a folder on your machine through the File System Access API. PreviewRich renders local previews in the browser.
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

### Manual browser test instances

Run these commands from `server/`. Create disposable fixture roots with
`mktemp`, then start each server command in a separate terminal. Set
`FIXTURES` to the printed directory in each terminal. The ports below are
examples; choose unused ports on your machine.

```bash
FIXTURES=$(mktemp -d)
printf '%s\n' "$FIXTURES"
mkdir -p "$FIXTURES"/{ui,keyboard-desktop,keyboard-mobile}
printf '# Browser UI\n' > "$FIXTURES/ui/README.md"
mkdir -p "$FIXTURES/keyboard-desktop/my-knowledge/docs/subdir"
printf '# Agent notes\n' > "$FIXTURES/keyboard-desktop/my-knowledge/AGENTS.md"
printf '# Topic\n\n[Next](subdir/next.md)\n' > "$FIXTURES/keyboard-desktop/my-knowledge/docs/topic.md"
printf '# Next\n' > "$FIXTURES/keyboard-desktop/my-knowledge/docs/subdir/next.md"
printf '# Root\n' > "$FIXTURES/keyboard-desktop/root-note.md"
ln -s my-knowledge "$FIXTURES/keyboard-desktop/prg"
printf '[Next](~/my-knowledge/docs/subdir/next.md)\n' > "$FIXTURES/keyboard-desktop/home-link.md"
cp -a "$FIXTURES/keyboard-desktop/." "$FIXTURES/keyboard-mobile/"

uv run filemill "$FIXTURES/ui" --port 8001
uv run filemill "$FIXTURES/keyboard-desktop" --port 8002
uv run filemill "$FIXTURES/keyboard-mobile" --port 8003
```

Open `http://127.0.0.1:8001` for the UI fixture, `http://127.0.0.1:8002`
for the desktop keyboard fixture, or `http://127.0.0.1:8003` for the mobile
keyboard fixture. These mirror the directory layouts used by
`test_browser_new_ui.py` and `test_browser_keyboard.py` for manual checks.
The automated suites create their own temporary roots and choose free ports.
Select a desktop, portrait or landscape viewport in the browser. Stop each
server with Ctrl-C, then remove the disposable fixture directory.

Quick start:

```bash
uv sync
timeout 1800 uv run pytest         # everything, browser tests included

# Only the real-browser tests. Install matching browsers first. The browser
# suite takes minutes on a 4-core host, so budget accordingly.
timeout 1800 uv run pytest tests/test_browser_keyboard.py tests/test_browser_new_ui.py
```

Do not add `--with`. `uv sync` installs the locked Playwright version.
Install its matching Chromium browser with `uv run playwright install chromium`.
If your environment already provides browsers, set `PLAYWRIGHT_BROWSERS_PATH`
to their directory and verify that their revision matches the locked release.
For a managed browser bundle, such as Nix, use that bundle's matching
Playwright release instead of downloading another browser.

## Architecture

```
src/filemill/
├── app.py          # Starlette app and routes
├── api.py          # /api/dir, /api/search, /api/raw, /api/preview
├── cli.py          # Typer CLI entry point
├── env.py          # FILEMILL_* variables, PYKOFINDER_* fallback
├── paths.py        # resolve_safe() and the named-mount map
├── preview.py      # Preview dispatcher (md / docx / pptx / pdf / img / code / raw)
├── pwa.py          # /manifest.json, /sw.js and /icons/ handlers
├── rendering.py    # markdown-it-py instance with plugins
├── urls.py         # View state and canonical URLs
├── vfs.py          # Virtual-filesystem registry + provider protocol
├── providers/      # VFS backends: SQLite, VTT, archives (tar, zip), Git bundles
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
