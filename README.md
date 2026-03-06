# pykofinder

A macOS Finder-style column-view file browser and previewer, served as a local
web application. Navigate directories by clicking column entries; previews render
inline for Markdown, DOCX, PPTX, PDF, images, plain text, and source code.

## Features

- **Column view** – multi-pane navigation à la macOS Finder
- **Rich previews** – Markdown (with plugins), DOCX, PPTX, PDF, images, plain text
- **Syntax highlighting** – source code files via Pygments "friendly" theme
- **Breadcrumb trail** – `~ / dir / subdir / file` navigation bar above the columns
- **URL sync** – browser URL stays in sync with the selected path; deep-link any location
- **Keyboard navigation** – `↑↓` move within a column; `→`/`Enter` open; `←` go back; `Esc` clear
- **Live reload** – `--live` flag restarts the server on code changes and refreshes the browser on content changes via SSE
- **Zoom** – expand preview pane to full viewport width
- **`.desktop` hyperlinks** – open service URLs directly from the browser
- **Symlink support** – safely follows symlink bookmarks in the configured root

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
uv sync --group test
uv run pytest          # unit + integration tests with coverage
```

## Architecture

```
src/pykofinder/
├── app.py          # FastHTML app, routes, _resolve_safe()
├── cli.py          # Typer CLI entry point
├── columns.py      # Column HTML generation + breadcrumb + pruning JS
├── preview.py      # Preview dispatcher (md / docx / pptx / pdf / img / code / raw)
├── rendering.py    # markdown-it-py instance with plugins
└── styles.py       # CSS + Pygments theme + HTMX + keyboard + live-reload JS
```

## License

MIT
