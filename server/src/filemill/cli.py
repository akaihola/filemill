import os
from pathlib import Path

import typer
import uvicorn

import filemill.app as app_module
from filemill.env import env, env_flag

cli = typer.Typer(help="Filemill – a column-view file browser and previewer")
_ROOT_ARGUMENT = typer.Argument(None, help="Root directory to browse")


@cli.command()
def main(
    root: Path | None = _ROOT_ARGUMENT,
    port: int = typer.Option(8000, help="Port to listen on"),
    live: bool = typer.Option(False, help="Enable live reload"),
    bind: str = typer.Option(
        env("BIND", "127.0.0.1"),
        "-b",
        "--bind",
        help="Address to bind to (overridden by FILEMILL_BIND env var)",
    ),
    public: bool = typer.Option(
        False,
        "--public",
        help="Never list or serve hidden files; FILEMILL_PUBLIC=1 does the same",
    ),
) -> None:
    """Start the Filemill web server."""
    resolved = (root or Path(".")).resolve()
    app_module.app.state.root = resolved
    # Either switch turns public mode on; nothing on the command line turns off
    # what the environment turned on.
    public = public or env_flag("PUBLIC")
    app_module.app.state.public = public

    if live:
        # uvicorn reload mode requires a string import path, so pass ROOT via env var
        os.environ["FILEMILL_ROOT"] = str(resolved)
        os.environ["FILEMILL_BIND"] = bind
        os.environ["FILEMILL_LIVE"] = "1"
        if public:
            os.environ["FILEMILL_PUBLIC"] = "1"
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
