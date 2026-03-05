# pykofinder

A macOS Finder-style column-view file browser and previewer, served as a local
web application. Navigate directories by clicking column entries; previews render
inline for Markdown, DOCX, PPTX, PDF, images, and more.

## Features

- **Column view** – multi-pane navigation à la macOS Finder
- **Rich previews** – Markdown (with plugins), DOCX, PPTX, PDF, images, plain text
- **Syntax highlighting** – code files via Pygments
- **Zoom** – expand preview pane to full viewport width
- **`.desktop` hyperlinks** – open service URLs directly from the browser
- **Symlink support** – safely follows symlinks within the configured root

## Installation

```bash
uv sync
```

## Usage

```bash
uv run pykofinder [--port PORT] [--live] [ROOT]
```

| Option   | Default | Description                                      |
| -------- | ------- | ------------------------------------------------ |
| `ROOT`   | `$PWD`  | Root directory to browse                         |
| `--port` | `8000`  | TCP port to listen on                            |
| `--live` | off     | Enable auto-reload on code changes (development) |

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development workflow and rules.

Quick start:

```bash
uv sync
uv run pytest          # run unit + integration tests
```

UI tests (Playwright):

```bash
uv run pytest tests/ui/
```

## Architecture

```
src/pykofinder/
├── app.py          # FastHTML app, routes, _resolve_safe()
├── cli.py          # Typer CLI entry point
├── columns.py      # Column HTML generation + pruning JS
├── preview.py      # Preview dispatcher (md / docx / pptx / pdf / img)
├── rendering.py    # markdown-it-py instance with plugins
└── styles.py       # CSS + Pygments theme + HTMX scroll JS
```

## License

MIT
