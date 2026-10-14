import re
import subprocess
import sys
from pathlib import Path

import yaml

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
    job = yaml.safe_load(
        (SERVER.parent / ".github" / "workflows" / "publish.yml").read_text()
    )["jobs"]["test"]
    steps = job["steps"]
    install_index = next(
        i
        for i, step in enumerate(steps)
        if "apt-get install -y ripgrep" in step.get("run", "")
    )
    assert steps[install_index]["if"] == "matrix.suite == 'server'"
    assert install_index < next(
        i for i, step in enumerate(steps) if step.get("run") == "${{ matrix.command }}"
    )


def test_ci_runs_independent_suites_after_lint_and_gates_publication():
    jobs = yaml.safe_load(
        (SERVER.parent / ".github" / "workflows" / "publish.yml").read_text()
    )["jobs"]
    test = jobs["test"]
    assert "strategy" in test, "The three suites still run serially in one job"
    assert test["needs"] == "lint"
    assert test["strategy"]["fail-fast"] is False
    assert "max-parallel" not in test["strategy"]
    assert test["strategy"]["matrix"]["include"] == [
        {
            "suite": "static-bundle",
            "command": "uv run --project server pytest static",
            "directory": ".",
        },
        {
            "suite": "static-development",
            "command": "uv run --project server pytest static --dev",
            "directory": ".",
        },
        {
            "suite": "server",
            "command": "uv run pytest --cov=src/filemill --cov-branch --cov-report=term-missing",
            "directory": "server",
        },
    ]
    steps = test["steps"]
    install = next(s for s in steps if "playwright install" in s.get("run", ""))
    assert (
        install["run"]
        == "uv run --project server playwright install --with-deps chromium"
    )
    assert "if" not in install
    suite = steps[-1]
    assert suite["run"] == "${{ matrix.command }}"
    assert suite["working-directory"] == "${{ matrix.directory }}"
    assert not test.get("continue-on-error", False)
    assert all(not step.get("continue-on-error", False) for step in steps)
    lint = "\n".join(s.get("run", "") for s in jobs["lint"]["steps"])
    for check in (
        "pre-commit run --all-files",
        "deno fmt --check ui/",
        "deno lint ui/",
        "deno run --allow-read=ui/core/model ui/core/model/test.mjs",
        "./build-index.py --check",
    ):
        assert check in lint
    publish = jobs["publish"]
    assert set(publish["needs"]) == {"lint", "test"}
    assert (
        publish["if"]
        == "github.ref == 'refs/heads/main' && github.event_name != 'pull_request'"
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


def test_ci_runs_every_suite_after_an_earlier_suite_fails():
    """A failing suite must not hide the next suite's results and durations.

    Run 38534616531 (2026-10-14) failed one static development test and so
    skipped the server suite entirely. The job still fails either way.
    """
    workflow = (SERVER.parent / ".github" / "workflows" / "publish.yml").read_text()
    for name in ("Test the shared sources", "Install ripgrep", "The server edition"):
        step = workflow.split(f"- name: {name}\n", 1)[1].split("\n\n", 1)[0]
        assert "if: ${{ !cancelled() }}" in step, name


def _workflow_concurrency() -> dict[str, str]:
    """The top-level `concurrency:` mapping of publish.yml, as raw strings."""
    workflow = (SERVER.parent / ".github" / "workflows" / "publish.yml").read_text()
    block = re.search(r"^concurrency:\n((?:  .*\n)+)", workflow, re.MULTILINE)
    assert block, "publish.yml has no workflow-level concurrency"
    return dict(line.strip().split(": ", 1) for line in block.group(1).splitlines())


def _evaluate(expression: str, workflow: str, ref: str) -> str:
    """Substitute the `github.workflow` and `github.ref` contexts like Actions."""
    context = {"github.workflow": workflow, "github.ref": ref}
    return re.sub(
        r"\$\{\{\s*([\w.]+)\s*\}\}", lambda m: context[m.group(1)], expression
    )


def test_ci_cancels_only_superseded_runs_of_the_same_ref():
    """A run may cancel only an older run of the same workflow and ref.

    The workflow-wide `group: pages` let any pull request cancel a main run or
    another pull request's tests. Main runs still share one group, which keeps
    Pages deployments serialized, since only main publishes.
    """
    concurrency = _workflow_concurrency()
    assert concurrency["cancel-in-progress"] == "true"
    group = concurrency["group"]
    assert "github.workflow" in group
    assert "github.ref" in group

    main = "refs/heads/main"
    pr_1, pr_2 = "refs/pull/1/merge", "refs/pull/2/merge"
    assert _evaluate(group, "publish", main) == _evaluate(group, "publish", main)
    assert _evaluate(group, "publish", pr_1) == _evaluate(group, "publish", pr_1)
    assert _evaluate(group, "publish", pr_1) != _evaluate(group, "publish", pr_2)
    assert _evaluate(group, "publish", main) != _evaluate(group, "publish", pr_1)
    assert _evaluate(group, "publish", main) != _evaluate(group, "other", main)


def test_ci_publishes_only_from_main_after_every_check():
    """Pull requests never publish; main publishes only after lint and tests."""
    workflow = (SERVER.parent / ".github" / "workflows" / "publish.yml").read_text()
    jobs = workflow.split("\njobs:", 1)[1]
    publish = jobs.split("\n  publish:\n", 1)[1]
    assert "\n  lint:\n" in jobs
    assert "\n  test:\n    needs: lint\n" in jobs
    assert publish.startswith(
        "    needs: test\n"
        "    if: github.ref == 'refs/heads/main'"
        " && github.event_name != 'pull_request'\n"
    )
