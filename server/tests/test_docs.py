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


def test_static_guide_ui_symlink_matches_checkout():
    guide = ROOT / "static/AGENTS.md"
    match = re.search(
        r"\[([^\]]+)\]\(([^)]+)\) is a \*\*symlink\*\* to "
        r"\[([^\]]+)\]\(([^)]+)\)",
        guide.read_text(),
    )
    assert match, "The static guide must state the UI symlink source and target"
    source_label, source_link, target_label, target_link = match.groups()
    source = guide.parent / source_link
    target = guide.parent / target_link
    assert source.is_symlink(), f"Documented source is not a symlink: {source_link}"
    assert source.resolve(strict=True) == target.resolve(strict=True)
    assert source_label == "ui/"
    assert target_label == "server/src/filemill/ui/"


def test_documentation_uses_portable_development_examples():
    setup = re.compile(
        r"\b(?:gogo|atom)\b|/home/(?:agent|akaihola)\b|~/prg/|~/repos/"
        r"|~/\.config/(?:coding-agents|hai)/|~/\.kandev/"
        r"|paivi/documents/|my-knowledge/pages/|repos/ai/|UV_CONSTRAINT"
    )
    paths = [
        *ROOT.rglob("*.md"),
        ROOT / "server/src/filemill/urls.py",
        ROOT / "server/pyproject.toml",
    ]
    found = []
    for path in paths:
        if any(part in {".git", ".venv", "vendor"} for part in path.parts):
            continue
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if setup.search(line):
                found.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    assert not found, "Development setup references:\n" + "\n".join(found)


@pytest.mark.parametrize(
    ("document", "obsolete"),
    [
        ("README.md", "pptx-vanilla-viewer"),
        ("server/README.md", "rendering.py"),
        ("server/CONTRIBUTING.md", "rendering.py"),
        ("server/CONTRIBUTING.md", "POST /api/render"),
        ("server/CONTRIBUTING.md", "preview-upload.js"),
        ("server/CONTRIBUTING.md", "100% branch coverage"),
        ("static/AGENTS.md", "There is no network"),
    ],
)
def test_current_edition_guidance_drops_retired_claims(document, obsolete):
    text = (ROOT / document).read_text()
    # Recorded measurements remain evidence, not current run instructions.
    current = text.split("### Historical local-folder measurements", 1)[0]
    assert obsolete not in current


def test_cli_documentation_distinguishes_arguments_from_asgi_environment():
    readme = (ROOT / "server/README.md").read_text()
    rows = [
        line.split("|")[1:-1] for line in readme.splitlines() if line.startswith("|")
    ]
    options = {cells[0].strip(): cells for cells in rows}
    assert options["`ROOT`"][2].strip() == "–"
    assert options["`--live`"][2].strip() == "–"


def test_readme_says_a_public_instance_must_use_public_mode():
    """[128]: the option, its variable and the requirement stay documented."""
    readme = (ROOT / "server/README.md").read_text()
    rows = [
        line.split("|")[1:-1] for line in readme.splitlines() if line.startswith("|")
    ]
    options = {cells[0].strip(): cells for cells in rows}
    assert options["`--public`"][2].strip() == "`FILEMILL_PUBLIC`"
    assert "A public instance must use `--public`" in readme


def test_dependency_policy_distinguishes_constraints_from_lock_selections():
    goals = (ROOT / "docs/GOALS.md").read_text()
    policy = next(p for p in goals.split("\n\n") if "**Few dependencies" in p)
    for concept in (
        "minimum supported versions",
        "deliberate bounded versions",
        "exact lockfile selections",
        "unverified",
    ):
        assert concept in policy, f"Dependency policy must explain {concept}"
    assert "each pin explained" not in policy


def test_decision_records_arrive_with_the_change():
    """[126]: no current rule lets a change land before its explanation."""
    review = (ROOT / "docs/ARCHITECTURE-REVIEW.md").read_text()
    rules = review.split("### Rules for changes", 1)[1].split("\n## ", 1)[0]
    rules = " ".join(rules.split())
    assert (
        "A decision that changes a port or a behaviour gets an ADR in the same"
        " change." in rules
    )
    roadmap = (ROOT / "docs/ROADMAP.md").read_text()
    assert "the same day" not in roadmap
    assert "[rules for changes]: ARCHITECTURE-REVIEW.md#rules-for-changes" in roadmap
    contributing = (ROOT / "CONTRIBUTING.md").read_text()
    assert "Update the documentation in the same commit as the change." in contributing


def test_architecture_summary_indexes_every_review_section():
    """[157]: agents read a short summary, then only the sections they need."""
    summary = ROOT / "docs/ARCHITECTURE-SUMMARY.md"
    assert summary.is_file(), "docs/ARCHITECTURE-SUMMARY.md is missing"
    size = len(summary.read_bytes())
    assert size <= 6144, f"The summary has {size} bytes; the limit is 6,144"
    index = summary.read_text().split("\n## Section index\n", 1)[1]
    review = (ROOT / "docs/ARCHITECTURE-REVIEW.md").read_text()
    headings = re.findall(r"^#{2,3} (.+)$", review, re.MULTILINE)
    missing = [heading for heading in headings if heading not in index]
    assert not missing, f"The summary's section index omits {missing}"


@pytest.mark.parametrize(
    "document", ["ui/core/icons.js", "ui/vendor/seti-map.js", "static/index.html"]
)
def test_icon_comments_do_not_require_a_missing_generator(document):
    """[127]: the committed icon assets have no tracked generator."""
    assert "build-seti-map.py" not in (ROOT / document).read_text()


def test_waiting_policy_distinguishes_slow_input_from_readiness():
    roadmap = (ROOT / "docs/ROADMAP.md").read_text()
    phase = roadmap.split("## Phase 7:", 1)[1].split("## Phase 8:", 1)[0]
    phase = " ".join(phase.split())
    assert "No test waits for a fixed time." not in phase
    assert "[condition-based waiting]" in phase
    assert (
        "[condition-based waiting]: ../server/CONTRIBUTING.md"
        "#wait-for-an-element-never-for-a-duration" in roadmap
    )
    guidance = (ROOT / "server/CONTRIBUTING.md").read_text()
    policy = guidance.split("### Wait for an Element, Never for a Duration", 1)[1]
    policy = " ".join(policy.split("## Submitting changes", 1)[0].split())
    # Keep the guarded API name out of this test source.
    wait_parts = ("wait_for", "timeout")
    for concept in (
        "test input",
        "not synchronization",
        "test_declined_json_member_recovers_after_refresh",
        "loading/error state",
        "DOM conditions",
        "_".join(wait_parts),
        "does not ban every sleep",
        "A delay alone does not prove overlap",
    ):
        assert concept in policy, f"Waiting policy must explain {concept}"
