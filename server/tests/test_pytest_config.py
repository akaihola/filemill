import subprocess
import sys
from pathlib import Path

SERVER = Path(__file__).parents[1]


def test_documented_command_from_server_loads_root_conftest():
    """`cd server && uv run pytest` must elect ../pytest.ini and its conftest.

    A `[tool.pytest.ini_options]` table in server/pyproject.toml would win the
    rootdir election and leave `client` and the other root fixtures unfound.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "tests/test_app.py::test_index_returns_200_with_title",
        ],
        cwd=SERVER,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert f"rootdir: {SERVER.parent}\n" in result.stdout
    assert "configfile: pytest.ini\n" in result.stdout
    assert result.returncode == 0, result.stdout
