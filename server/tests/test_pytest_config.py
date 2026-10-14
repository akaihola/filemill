import re
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


def test_ci_installs_browsers_for_the_locked_playwright():
    """CI must download the browsers of the Playwright that uv.lock resolves.

    The tests run under `uv run --project server`, so a `pip install
    "playwright==X"` before `playwright install` fetches browsers for X while
    the tests launch with the locked version. Run 37975040277 (2026-10-09) lost
    every browser test that way: "Executable doesn't exist at
    .../chromium_headless_shell-1243/...". Installing through the project's
    environment leaves no second version to drift.
    """
    workflow = (SERVER.parent / ".github" / "workflows" / "publish.yml").read_text()
    assert "playwright==" not in workflow
    assert "uv run --project server playwright install --with-deps chromium" in workflow


def test_ci_installs_ripgrep_before_the_server_suite():
    """The server shells out to ripgrep; the runner image lacks it.

    Run 38155597653 (2026-10-11) failed every search test with
    "Search is unavailable: ripgrep is not installed".
    """
    workflow = (SERVER.parent / ".github" / "workflows" / "publish.yml").read_text()
    assert workflow.index("apt-get install -y ripgrep") < workflow.index(
        "name: The server edition"
    )


def test_ci_reports_the_slowest_tests_of_each_suite():
    """Every CI pytest run prints its 20 slowest setup, call and teardown phases.

    Run 38155597653 (2026-10-11) logged only suite totals, so the time spent in
    browser fixtures could not be told apart from the tests. Each suite runs in
    its own named step, which keeps the three reports apart in the log.
    """
    workflow = (SERVER.parent / ".github" / "workflows" / "publish.yml").read_text()
    runs = [
        line.strip()
        for line in workflow.splitlines()
        if re.search(r"\buv run (--project server )?pytest\b", line)
    ]
    assert len(runs) == 3
    assert all("--durations=20" in run for run in runs), runs
    steps = [
        line.split("name:", 1)[1].strip()
        for line in workflow.splitlines()
        if line.strip().startswith("- name:")
    ]
    assert {
        "Test the bundle",
        "Test the shared sources",
        "The server edition",
    } <= set(steps)
