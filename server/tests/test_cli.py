import os
from unittest.mock import MagicMock

import uvicorn
from typer.testing import CliRunner

import filemill.app as app_module
import filemill.cli as cli_module
from filemill.cli import cli, entry_point

runner = CliRunner()


def test_entry_point_calls_cli(monkeypatch):
    """entry_point() must delegate to the module-level cli Typer app."""
    mock_cli = MagicMock()
    monkeypatch.setattr(cli_module, "cli", mock_cli)
    entry_point()
    mock_cli.assert_called_once()


def test_main_live_false_passes_app_object(tmp_path, monkeypatch):
    """live=False → uvicorn.run receives the app object (not a string)."""
    mock_run = MagicMock()
    monkeypatch.setattr(uvicorn, "run", mock_run)
    result = runner.invoke(cli, [str(tmp_path), "--port", "9001"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] is app_module.app
    assert kwargs.get("port") == 9001


def test_main_live_true_passes_string_and_reload(tmp_path, monkeypatch):
    """live=True → uvicorn.run receives the import-string, reload=True, env var set."""
    mock_run = MagicMock()
    monkeypatch.setattr(uvicorn, "run", mock_run)
    monkeypatch.delenv(
        "FILEMILL_ROOT", raising=False
    )  # ensure clean state; restored by monkeypatch
    result = runner.invoke(cli, [str(tmp_path), "--port", "9002", "--live"])
    assert result.exit_code == 0
    args, kwargs = mock_run.call_args
    assert args[0] == "filemill.app:app"
    assert kwargs.get("reload") is True
    assert os.environ.get("FILEMILL_ROOT") == str(tmp_path.resolve())


def test_main_default_root_uses_cwd(tmp_path, monkeypatch):
    """root=None → ROOT is set to cwd (Path('.').resolve())."""
    mock_run = MagicMock()
    monkeypatch.setattr(uvicorn, "run", mock_run)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert app_module.ROOT == tmp_path


def test_default_bind_is_loopback(tmp_path, monkeypatch):
    mock_run = MagicMock()
    monkeypatch.delenv("FILEMILL_BIND", raising=False)
    monkeypatch.delenv("BIND", raising=False)
    monkeypatch.setattr(uvicorn, "run", mock_run)
    result = runner.invoke(cli, [str(tmp_path)])
    assert result.exit_code == 0
    assert mock_run.call_args.kwargs["host"] == "127.0.0.1"


def test_default_bind_is_loopback_live(tmp_path, monkeypatch):
    mock_run = MagicMock()
    monkeypatch.delenv("FILEMILL_BIND", raising=False)
    monkeypatch.delenv("BIND", raising=False)
    monkeypatch.setattr(uvicorn, "run", mock_run)
    result = runner.invoke(cli, [str(tmp_path), "--live"])
    assert result.exit_code == 0
    assert mock_run.call_args.kwargs["host"] == "127.0.0.1"


# ── #16 bind address option ───────────────────────────────────────────────────


def test_serve_has_bind_option():
    from typer.testing import CliRunner

    from filemill.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert "--bind" in result.output or "-b" in result.output


def test_bind_option_passed_to_uvicorn_normal(tmp_path, monkeypatch):
    """--bind value is forwarded as host= in the non-live branch."""
    mock_run = MagicMock()
    monkeypatch.setattr(uvicorn, "run", mock_run)
    result = runner.invoke(cli, [str(tmp_path), "--bind", "127.0.0.1"])
    assert result.exit_code == 0
    _, kwargs = mock_run.call_args
    assert kwargs.get("host") == "127.0.0.1"


def test_bind_option_passed_to_uvicorn_live(tmp_path, monkeypatch):
    """--bind value is forwarded as host= in the live/reload branch."""
    mock_run = MagicMock()
    monkeypatch.setattr(uvicorn, "run", mock_run)
    result = runner.invoke(cli, [str(tmp_path), "--live", "--bind", "127.0.0.1"])
    assert result.exit_code == 0
    _, kwargs = mock_run.call_args
    assert kwargs.get("host") == "127.0.0.1"
    assert kwargs.get("reload") is True
