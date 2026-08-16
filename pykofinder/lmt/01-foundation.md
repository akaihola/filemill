# Milestone 01 – Foundation

pykofinder is a macOS Finder-style column-view file browser and previewer,
served as a local web application built with FastHTML. In this first milestone
we lay the ground: a `pyproject.toml` that declares every dependency the
finished project will need, an empty package marker, and a tiny CLI stub that
proves the package installs and responds to `--help`.

## Build configuration

The project uses `uv` as its package manager and build backend. We declare
all runtime dependencies up front – even those whose code we won't write
until later milestones – so that `uv sync` creates a complete virtual
environment from the start.

```toml pyproject.toml
[project]
name = "pykofinder"
version = "0.1.0"
description = "macOS Finder column-view file manager and previewer"
requires-python = ">=3.12"
dependencies = [
    "python-fasthtml>=0.12",
    "markdown-it-py",
    "mdit-py-plugins",
    "pygments",
    "mammoth",
    "python-pptx",
    "typer",
    "watchfiles>=0.21",
    "linkify-it-py>=2.1.0",
]

[project.scripts]
pykofinder = "pykofinder.cli:entry_point"

[build-system]
requires = ["uv_build>=0.6.6,<0.7"]
build-backend = "uv_build"

[dependency-groups]
dev = [
    "pytest>=8",
    "httpx>=0.27",
    "pytest-cov>=5",
    "playwright>=1.57.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src/pykofinder --cov-branch --cov-report=term-missing"
markers = [
    "integration: tests that launch a real browser or server process",
]
```

Key choices:

- **python-fasthtml** provides the ASGI framework with HTMX integration.
- **markdown-it-py** + **mdit-py-plugins** power the Markdown preview pipeline.
- **pygments** handles syntax highlighting for both code previews and the
  Markdown fenced-code renderer.
- **mammoth** and **python-pptx** convert DOCX and PPTX to HTML.
- **typer** gives us a CLI with automatic `--help` generation.
- **watchfiles** watches the filesystem for the live-reload feature.

## Package marker

The package init is empty – it simply marks `src/pykofinder/` as a Python
package.

<!--
```python src/pykofinder/__init__.py
```
-->

## CLI stub

We start with a minimal Typer application. It accepts no arguments yet and
just prints a placeholder message. The real CLI comes in Milestone 7 once
the web application exists; for now we only need `entry_point()` so that
`uv run pykofinder --help` works.

```python src/pykofinder/cli.py
import typer

cli = typer.Typer(help="pykofinder – macOS Finder-style column-view file browser")


@cli.command()
def main() -> None:
    """Start the pykofinder web server."""
    print("pykofinder – not yet implemented (see later milestones)")


def entry_point() -> None:
    """Entry point for the pykofinder script."""
    cli()


if __name__ == "__main__":  # pragma: no cover
    cli()
```

## Verification

```bash
rm -rf _tangle_out && mkdir _tangle_out && cd _tangle_out
lmt ../01-foundation.md
uv sync
uv run pykofinder --help
```

You should see Typer's auto-generated help text listing the `main` command.
