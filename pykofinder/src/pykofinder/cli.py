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
