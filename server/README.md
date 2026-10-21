# Filemill — server edition

Filemill is a column-view file browser and previewer. The server edition is a
local web application in Python. Click a column entry to open a directory.
Previews show inline. PPTX previews extract slide text; they do not reproduce
slide layout.

The [repository README] has the current edition/renderer table
and implementation links. This document covers the Python edition.

## Features

- **Column view** – multi-pane navigation in the style of macOS Finder
- **Rich previews** – Markdown (with plugins), DOCX, PPTX, PDF, images, plain text, and source code highlighted in the browser; Pygments ("friendly" theme) colours archive members
- **Markdown extras** – wikilinks (`[[PageName]]`), plain-URL links, relative-link normalisation
- **Virtual filesystem** – a SQLite database opens as table → row columns; JSON and JSONL files open through the shared browser adapter; a tar (`.tar`, `.tar.gz`, `.tar.bz2`, `.tar.xz`, `.tar.zst`) or zip archive opens as columns of its members, and a member previews as the file it is; a Git `.bundle` opens as columns of its refs (`heads/main`, `tags/v1`, `HEAD`) and then its trees, when `git` is installed
- **Static web server** – root-relative file URLs serve bytes with the correct Content-Type. Direct symlink children of ROOT act as bookmarks. `/w/` and `/n/` are ordinary file paths ([ADR 0088]).
- **Finder URLs** – the URL path is the file path relative to the root, for example `/docs/readme.md`. A deep link opens any location. `/sample.db/users/1` opens one database row
- **Dotfiles** – on a private instance, add `?hidden=show` to show them; public mode refuses hidden paths
- **Keyboard navigation** – `↑↓` move in a column; `→`/`Enter` open; `←` goes back; `Home`/`End`/`PgUp`/`PgDn` scroll
- **Live reload** – the `--live` CLI flag enables Uvicorn reload, as implemented in [server/src/filemill/cli.py]
- **`.desktop` files** – show as a link card
- **Symlink bookmarks** – a direct symlink child of the root opens as a bookmark, and its target subtree is browsable
- **Open Folder…** – the served page can browse a folder on your machine through the File System Access API. PreviewRich renders local previews in the browser.
- **PWA** – installable, with a manifest, service worker and icons. The [worker] asks the server first for every read but a content-hashed UI module, so an online read is never an older copy, and keeps what it read as offline copies. While the server is offline, folders and files read earlier stay readable, read-only, and an indicator in the top bar says so. See [Installed PWA].

## Installation

Run these commands from [server/] in a checkout. Python 3.12 or newer and
`uv` are required. Content search needs `rg`; Git bundle browsing needs `git`.

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
| `--public`      | off       | `FILEMILL_PUBLIC` | Read-only; never list or serve hidden files |

[server/src/filemill/cli.py] resolves the positional root, defaulting to
the working directory, and passes `--port`, `--bind` and `--live` to Uvicorn.
`FILEMILL_ROOT` does not select the CLI root; `FILEMILL_LIVE` does not enable
CLI reload. For direct ASGI loading, [server/src/filemill/app.py] reads
`FILEMILL_ROOT`, defaulting to the home directory. CLI reload passes its resolved
root through that variable. [server/src/filemill/env.py] provides legacy
`PYKOFINDER_*` fallbacks when the corresponding `FILEMILL_*` value is unset or
empty. The CLI bind default uses that lookup; an explicit `--bind` takes
precedence. `FILEMILL_LIVE` is written by `--live` but has no reader in the
application. It is not a standalone reload setting.

`FILEMILL_ORIGINS` defaults to empty, allowing loopback hosts only. Configure
exact space-separated origins for a LAN address or reverse proxy; see the
[authorization policy].
`window.FILEMILL_CDN` is a browser module map supplied by the shell, not a
server environment variable.

### Public instances

A public instance must use `--public`, or set `FILEMILL_PUBLIC=1`. Any value
but empty, `0`, `false`, `no` or `off` turns the mode on, and either switch is
enough. Values are stripped and compared without case. Public roots are
read-only and exclude hidden paths. The [security policy]
owns the full rule, bookmark boundaries, Host configuration and limits.
The mode passes through `--live` reloads and direct ASGI loading.

## Installed PWA

The installed app connects to the Filemill server on its own origin. Start the
local service first:

```bash
uv run filemill [ROOT]
```

The default listener is `127.0.0.1:8000`, so only this machine can reach it.
The PWA cannot start a native process. Use `--bind` only when you want to
expose the server beyond loopback.

When the server stops, the open page keeps what it shows, and a
**Server offline** indicator appears in the top bar within 30 seconds, or at
the next read. Click or tap it, or focus it and press Enter or Space, to see
what that means, the start command and **Retry now**. Filemill also retries
every 5 seconds. When the server answers again, the indicator says
**Server back online**, and folders and files read while it was offline are
read again. A restarted server has a new mutation token; the page fetches it,
so saving works without a reload. After a restart the page did not notice, a
save shows **Change refused**; Retry now fetches the new token.

After one visit under the installed worker, opening the app while the server
is stopped shows the copies of the folders and files read before, with the
indicator. Copies are read-only, and saves and deletes fail with
"Server offline". A folder never read says "Not available offline". An
address the worker has no shell for, such as a file's own URL, or a first
visit without a worker, gets the [recovery page]
with the start command and a retry button. The worker keeps up to 200 reads of at most 2 MiB each; see
[ADR 0089].

## Development

Read [server/CONTRIBUTING.md] for the development rules.

### Manual browser test instances

Run these commands from [server/]. Create disposable fixture roots with
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

[server/CONTRIBUTING.md] has the test commands and the
browser setup.

## Architecture

The [root README] describes the shared ports, renderer choices
and the single frontend under [server/src/filemill/ui/]. The
[contributor guide] maps the Python modules.
[server/src/filemill/app.py] serves the shell at root-relative
render/highlight URLs; bare file URLs serve bytes, and directory indexes take
precedence over the shell. Symlink containment and mutation authorization were
fixed in [103].
See [SECURITY.md] for write authority and remaining trust limits.

## License

MIT

[repository README]: ../README.md
[ADR 0088]: ../docs/adr/0088-remove-named-mount-and-alternate-shell-routes.md
[server/src/filemill/cli.py]: src/filemill/cli.py
[worker]: src/filemill/static/sw.js
[Installed PWA]: #installed-pwa
[server/src/filemill/app.py]: src/filemill/app.py
[server/src/filemill/env.py]: src/filemill/env.py
[authorization policy]: ../SECURITY.md#save-and-delete-authorization
[security policy]: ../SECURITY.md
[recovery page]: src/filemill/static/sw.js
[ADR 0089]: ../docs/adr/0089-an-offline-server-shows-older-copies-with-an-indicator.md
[server/CONTRIBUTING.md]: CONTRIBUTING.md
[root README]: ../README.md
[contributor guide]: CONTRIBUTING.md#source-layout
[103]: ../docs/tasks/103-close-the-directory-index-path-escape-and-authorize-save-and-delete-a1.md
[SECURITY.md]: ../SECURITY.md
[server/]: ./
[server/src/filemill/ui/]: src/filemill/ui/
