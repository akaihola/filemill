import os
from pathlib import Path

import typer
import uvicorn

import filemill.app as app_module
from filemill.env import env

cli = typer.Typer(help="Filemill – a column-view file browser and previewer")


@cli.command()
def main(
    root: Path | None = typer.Argument(  # noqa: B008
        None, help="Root directory to browse"
    ),
    port: int = typer.Option(8000, help="Port to listen on"),
    live: bool = typer.Option(False, help="Enable live reload"),
    bind: str = typer.Option(
        env("BIND", "127.0.0.1"),
        "-b",
        "--bind",
        help="Address to bind to (overridden by FILEMILL_BIND env var)",
    ),
) -> None:
    """Start the Filemill web server."""
    resolved = (root or Path(".")).resolve()
    app_module.ROOT = resolved

    if live:
        # uvicorn reload mode requires a string import path, so pass ROOT via env var
        os.environ["FILEMILL_ROOT"] = str(resolved)
        os.environ["FILEMILL_BIND"] = bind
        os.environ["FILEMILL_LIVE"] = "1"
        uvicorn.run(
            "filemill.app:app",
            host=bind,
            port=port,
            reload=True,
        )
    else:
        uvicorn.run(app_module.app, host=bind, port=port)


def entry_point() -> None:
    """Entry point for the filemill script."""
    cli()


if __name__ == "__main__":  # pragma: no cover
    cli()
