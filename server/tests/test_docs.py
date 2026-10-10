"""The documents must not contradict the pins and the code they describe.

One Playwright version repeated across READMEs and script docstrings goes
stale at every bump, and a stale `--with "playwright==X"` overrides the lock
and fails at BrowserType.launch. Historical records (ADRs, completed task
descriptions) are exempt: they state what was measured, not what to run.
"""

import re
from pathlib import Path

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

PIN = re.compile(r"playwright\s*[~=]=\s*(\d+\.\d+)")


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
