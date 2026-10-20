# Filemill — server edition

Filemill is a column-view file browser and previewer. The server edition is a
local web application in Python. Click a column entry to open a directory.
Previews show inline. PPTX previews extract slide text; they do not reproduce
slide layout.

The [repository README](../README.md) has the current edition/renderer table
and implementation links. This document covers the Python edition.

## Features

- **Column view** – multi-pane navigation in the style of macOS Finder
- **Rich previews** – Markdown (with plugins), DOCX, PPTX, PDF, images, plain text, and source code highlighted in the browser; Pygments ("friendly" theme) colours archive members
- **Markdown extras** – wikilinks (`[[PageName]]`), plain-URL links, relative-link normalisation
- **Virtual filesystem** – a SQLite database opens as table → row columns; JSON and JSONL files open through the shared browser adapter; a tar (`.tar`, `.tar.gz`, `.tar.bz2`, `.tar.xz`, `.tar.zst`) or zip archive opens as columns of its members, and a member previews as the file it is; a Git `.bundle` opens as columns of its refs (`heads/main`, `tags/v1`, `HEAD`) and then its trees, when `git` is installed
- **Static web server** – `/w/<mount>/<path>` serves a file under a named mount with the correct Content-Type. The root directory is mounted as `/w/<ROOT.name>/...`. Each direct symlink child of ROOT is mounted under its own name
- **Finder URLs** – the URL path is the file path relative to the root, for example `/docs/readme.md`. A deep link opens any location. `/sample.db/users/1` opens one database row
- **Dotfiles** – add `?hidden=show` to the URL to show them
- **Keyboard navigation** – `↑↓` move in a column; `→`/`Enter` open; `←` goes back; `Home`/`End`/`PgUp`/`PgDn` scroll
- **Live reload** – the `--live` CLI flag enables Uvicorn reload, as implemented in [cli.py](src/filemill/cli.py)
- **`.desktop` files** – show as a link card
- **Symlink bookmarks** – a direct symlink child of the root opens as a bookmark, and its target subtree is browsable
- **Open Folder…** – the served page can browse a folder on your machine through the File System Access API. PreviewRich renders local previews in the browser.
- **PWA** – installable, with a manifest, service worker and icons. The [worker](src/filemill/static/sw.js) bypasses `/api/` and sends navigations to the network, but caches other same-origin GETs, such as images and `/w/` files that a page embeds. A5 remains open; cold offline recovery is not reliable. See the [architecture review](../docs/ARCHITECTURE-REVIEW.md).

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
| `ROOT`          | `$PWD`    | –   | Root directory to browse         |
| `--port`        | `8000`    | –                   | TCP port to listen on            |
| `--bind` / `-b` | `127.0.0.1` | `FILEMILL_BIND` | Network interface to bind to |
| `--live`        | off       | – | Enable auto-reload (development) |
| `--public`      | off       | `FILEMILL_PUBLIC` | Never list or serve hidden files |

[`cli.py`](src/filemill/cli.py) resolves the positional root, defaulting to
the working directory, and passes `--port`, `--bind` and `--live` to Uvicorn.
`FILEMILL_ROOT` does not select the CLI root; `FILEMILL_LIVE` does not enable
CLI reload. For direct ASGI loading, [`app.py`](src/filemill/app.py) reads
`FILEMILL_ROOT`, defaulting to the home directory. CLI reload passes its resolved
root through that variable. [`env.py`](src/filemill/env.py) provides legacy
`PYKOFINDER_*` fallbacks; the CLI bind default uses that lookup, while an explicit
`--bind` takes precedence.

### Public instances

A public instance must use `--public`, or set `FILEMILL_PUBLIC=1`. Any value
but empty, `0`, `false`, `no` or `off` turns the mode on, and either switch is
enough. A public instance answers 404 for any path with a component that starts
with `.`, whatever the query string says, `?hidden=show` included, and does not
follow a symlink into such a path. Listings and search results leave those
entries out. [`cli.py`](src/filemill/cli.py) passes the mode to `--live`
reloads through the variable, and [`app.py`](src/filemill/app.py) reads it for
direct ASGI loading.
[ADR 0087](../docs/adr/0087-a-public-instance-never-lists-or-serves-hidden-paths.md)
gives the rule and what it does not hide.

## Installed PWA

The installed app connects to the Filemill server on its own origin. Start the
local service first:

```bash
uv run filemill [ROOT]
```

The default listener is `127.0.0.1:8000`, so only this machine can reach it.
The PWA cannot start a native process. The
[recovery page](src/filemill/static/sw.js) offers a start command and retry
button, but A5 means an uncached offline navigation may not reach it.
Use `--bind` only when you want to
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

[CONTRIBUTING.md](CONTRIBUTING.md#running-tests) has the test commands and the
browser setup.

## Architecture

The [root README](../README.md) describes the shared ports, renderer choices
and the single frontend under `src/filemill/ui/`. The
[contributor guide](CONTRIBUTING.md#source-layout) maps the Python modules.
[`app.py`](src/filemill/app.py) serves the shell at `/n/` and root-relative
render/highlight URLs; bare file URLs serve bytes, and directory indexes take
precedence over the shell. Symlink containment and mutation authorization were
fixed in [103](../docs/tasks/103-close-the-directory-index-path-escape-and-authorize-save-and-delete-a1.md).
See [SECURITY.md](../SECURITY.md) for write authority and remaining trust limits.

## License

MIT
