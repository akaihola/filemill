import os
from pathlib import Path
from typing import Optional

import typer

from filemill.env import env

cli = typer.Typer(help="Filemill – a column-view file browser and previewer")


@cli.command()
def main(
    root: Optional[Path] = typer.Argument(None, help="Root directory to browse"),
    port: int = typer.Option(8000, help="Port to listen on"),
    live: bool = typer.Option(False, help="Enable live reload"),  # noqa: FBT001
    bind: str = typer.Option(
        env("BIND", "0.0.0.0"),
        "-b",
        "--bind",
        help="Address to bind to (overridden by FILEMILL_BIND env var)",
    ),
) -> None:
    """Start the Filemill web server."""
    import uvicorn

    import filemill.app as app_module

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
