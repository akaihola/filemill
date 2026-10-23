"""Browser startup belongs only to the root fixture owner."""

import ast
from pathlib import Path


def test_browser_lifecycles_belong_to_root_fixtures():
    root = Path(__file__).parents[2]
    offenders = []
    for directory in (root / "server/tests", root / "static/tests"):
        for path in directory.rglob("*.py"):
            tree = ast.parse(path.read_text())
            for call in ast.walk(tree):
                if not isinstance(call, ast.Call):
                    continue
                name = (
                    call.func.attr
                    if isinstance(call.func, ast.Attribute)
                    else call.func.id
                    if isinstance(call.func, ast.Name)
                    else ""
                )
                if name in {
                    "sync_playwright",
                    "async_playwright",
                    "launch",
                    "launch_persistent_context",
                }:
                    offenders.append(f"{path.relative_to(root)}:{call.lineno}")
    assert not offenders, "Browser lifecycles outside root fixtures: " + ", ".join(
        offenders
    )
