"""First-party Python noqa comments must link to a focused issue."""

import io
import re
import subprocess
import tokenize
from pathlib import Path

import pytest


def unlinked_noqa(source):
    return [
        token.start[0]
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.COMMENT
        and re.search(
            r"#\s*(?:(?:ruff|flake8):\s*)?noqa\b", token.string, re.IGNORECASE
        )
        and not re.search(r"\bdocs/tasks/[0-9]+-[\w-]+\.md\b", token.string)
    ]


@pytest.mark.parametrize(
    ("source", "lines"),
    [
        ("x = 1  # noqa\n", [1]),
        ("x = 1  # noqa: F401 -- intentional\n", [1]),
        ("# ruff: noqa: F401\n", [1]),
        ("# flake8: noqa\n", [1]),
        ("x = 1  # NOQA: F401\n", [1]),
        ("x = 1  # noqa: F401 -- docs/ARCHITECTURE-REVIEW.md\n", [1]),
        ("# ruff: noqa -- docs/tasks/24-split-app-py.md\n", []),
        ("x = 1  # noqa: F401 -- docs/tasks/24-split-app-py.md\n", []),
        ('text = "# noqa"\n', []),
        ('"""# noqa: F401"""\n', []),
    ],
)
def test_suppression_link_syntax(source, lines):
    assert unlinked_noqa(source) == lines


def test_first_party_suppressions_link_issues():
    root = Path(__file__).parents[2]
    paths = (
        subprocess.check_output(["git", "ls-files", "-z", "--", "*.py"], cwd=root)
        .decode()
        .split("\0")
    )
    offenders = [
        f"{name}:{line}"
        for name in paths
        if name
        for line in unlinked_noqa((root / name).read_text())
    ]
    assert not offenders, "Unlinked suppressions: " + ", ".join(offenders)
