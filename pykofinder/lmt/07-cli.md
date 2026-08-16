# Milestone 07 – Command-line interface

The placeholder CLI from Milestone 1 served us while we built the
application. Now we replace it with the real Typer-based entry point that
wires `ROOT`, `--port`, `--bind`, and `--live` into uvicorn.

## Full CLI

Our simple stub from Milestone 1 printed a placeholder message. Now that
`pykofinder.app` exists, the CLI can import it, set `ROOT`, and start the
server.

Two modes exist:

- **Normal mode** – pass the already-imported `app` object directly to
  uvicorn. Efficient, no re-import overhead.
- **Live-reload mode** – uvicorn is given the _string_ `"pykofinder.app:app"`
  and `reload=True`. When source files change, uvicorn re-imports the
  module, which re-reads the env-var-backed `ROOT` and `LIVE_MODE`
  globals. We set those env vars here before handing off.

```python src/pykofinder/cli.py
import os
from pathlib import Path
from typing import Optional

import typer

cli = typer.Typer(help="pykofinder – macOS Finder-style column-view file browser")


@cli.command()
def main(
    root: Optional[Path] = typer.Argument(None, help="Root directory to browse"),
    port: int = typer.Option(8000, help="Port to listen on"),
    live: bool = typer.Option(False, help="Enable live reload"),  # noqa: FBT001
    bind: str = typer.Option(
        os.environ.get("PYKOFINDER_BIND", "0.0.0.0"),
        "-b",
        "--bind",
        help="Address to bind to (overridden by PYKOFINDER_BIND env var)",
    ),
) -> None:
    """Start the pykofinder web server."""
    import uvicorn

    import pykofinder.app as app_module

    resolved = (root or Path(".")).resolve()
    app_module.ROOT = resolved

    if live:
        # uvicorn reload mode requires a string import path, so pass ROOT via env var
        os.environ["PYKOFINDER_ROOT"] = str(resolved)
        os.environ["PYKOFINDER_BIND"] = bind
        os.environ["PYKOFINDER_LIVE"] = "1"
        uvicorn.run(
            "pykofinder.app:app",
            host=bind,
            port=port,
            reload=True,
        )
    else:
        uvicorn.run(app_module.app, host=bind, port=port)


def entry_point() -> None:
    """Entry point for the pykofinder script."""
    cli()


if __name__ == "__main__":  # pragma: no cover
    cli()
```

## Verification

```bash
rm -rf _tangle_out && mkdir _tangle_out && cd _tangle_out
lmt ../01-*.md ../02-*.md ../03-*.md ../04-*.md ../05-*.md ../06-*.md ../07-*.md
uv sync
uv run pykofinder --help
```

The help output should now show all options: `ROOT`, `--port`, `--bind`, and
`--live`. Running `uv run pykofinder /tmp --port 9000` should start a
working web server browsing `/tmp`.
