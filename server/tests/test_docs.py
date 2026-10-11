"""The documents must not contradict the pins and the code they describe.

One Playwright version repeated across READMEs and script docstrings goes
stale at every bump, and a stale `--with "playwright==X"` overrides the lock
and fails at BrowserType.launch. Historical records (ADRs, completed task
descriptions) are exempt: they state what was measured, not what to run.
"""

import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]

LIVE_DOCS = [
    *ROOT.glob("*.md"),
    *(ROOT / "server").glob("*.md"),
    *(ROOT / "static").glob("*.md"),
    *(ROOT / "static").glob("*.py"),
    *(ROOT / "ui").rglob("*.md"),
    *(ROOT / ".github" / "workflows").glob("*.yml"),
    ROOT / "docs" / "ARCHITECTURE-REVIEW.md",
    ROOT / "docs" / "GOALS.md",
]

PIN = re.compile(
    r"\bplaywright(?:\s*[~=]=\s*|\s+(?=\d+\.\d+\.(?:\d+|x)\b))(\d+\.\d+)",
    re.IGNORECASE,
)


def pinned_version() -> str:
    pyproject = (ROOT / "server" / "pyproject.toml").read_text()
    match = re.search(r'^\s*"playwright~=(\d+\.\d+)\.\d+",', pyproject, re.MULTILINE)
    assert match, "server/pyproject.toml must pin playwright~=X.Y.Z"
    return match.group(1)


def recorded_failure(lines: list[str], index: int) -> bool:
    """A version shown as a measured failure may stay; it is not advice."""
    window = " ".join(lines[index : index + 4])
    return "fail" in window or "Executable doesn't exist" in window


def test_live_documents_name_only_the_pinned_playwright():
    pinned = pinned_version()
    stale = []
    for path in LIVE_DOCS:
        if not path.is_file():
            continue
        lines = path.read_text().splitlines()
        for index, line in enumerate(lines):
            for version in PIN.findall(line):
                if version != pinned and not recorded_failure(lines, index):
                    stale.append(
                        f"{path.relative_to(ROOT)}:{index + 1}: {line.strip()}"
                    )
    assert not stale, "\n".join(stale)


@pytest.mark.parametrize(
    ("text", "rejected"),
    [
        (
            (
                "Prerequisites: `uv`, a graphical desktop, the repository's Playwright "
                "1.61.0\nenvironment with its matching Chromium browser, and port `8787` "
                "free."
            ),
            True,
        ),
        ('uv run --with "playwright==1.61.0" pytest', True),
        ("playwright~=1.61", True),
        ("Playwright 1.61.x environment", True),
        ("Playwright 1.61.0\nfailed to launch the Nix browser.", False),
        ("playwright==1.61.0\nExecutable doesn't exist", False),
        (f"Playwright {pinned_version()}.0 environment", False),
        ("Update stale Playwright 1.61 pins and the server renderer note", False),
    ],
)
def test_playwright_guard_checks_prose_and_preserves_measurements(
    tmp_path, monkeypatch, text, rejected
):
    pyproject = (ROOT / "server" / "pyproject.toml").read_text()
    (tmp_path / "server").mkdir()
    (tmp_path / "server" / "pyproject.toml").write_text(pyproject)
    (tmp_path / "static").mkdir()
    checklist = tmp_path / "static" / "FSA-TEST-CHECKLIST.md"
    checklist.write_text(text)
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    monkeypatch.setattr(sys.modules[__name__], "LIVE_DOCS", [checklist])
    if rejected:
        with pytest.raises(AssertionError, match="FSA-TEST-CHECKLIST"):
            test_live_documents_name_only_the_pinned_playwright()
    else:
        test_live_documents_name_only_the_pinned_playwright()


def test_server_test_guidance_runs_from_server():
    contributing = (ROOT / "server" / "CONTRIBUTING.md").read_text()
    match = re.search(
        r"overrides the pin, so run the suites with `([^`]+)`", contributing
    )
    assert match, "CONTRIBUTING.md must give a test command without --with"
    result = subprocess.run(
        [
            *shlex.split(match.group(1)),
            "--collect-only",
            "-q",
            "tests/test_docs.py",
        ],
        cwd=ROOT / "server",
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "test_live_documents_name_only_the_pinned_playwright" in result.stdout


def test_adapters_readme_matches_app_http_renderers():
    app = (ROOT / "ui" / "adapters" / "app-http.js").read_text()
    match = re.search(r"\[([^\]]*)\]\.includes\(e\.kind\)", app)
    assert match, "app-http.js must filter RICH_RENDERERS by a literal kind list"
    kinds = set(re.findall(r'"(\w+)"', match.group(1))) - {"offline"}
    readme = (ROOT / "ui" / "adapters" / "README.md").read_text()
    paragraph = next(p for p in readme.split("\n\n") if "`app-http.js` adds" in p)
    names = {
        "md": "Markdown",
        "markdown": "Markdown",
        "docx": "`.docx`",
        "pptx": "`.pptx`",
    }
    missing = sorted(names[k] for k in kinds if names[k] not in paragraph)
    assert not missing, f"README omits browser renderers: {missing}"
    assert "only `.pptx`" not in paragraph
