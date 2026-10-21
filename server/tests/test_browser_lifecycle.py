"""Browser lifetimes belong to fixtures, including helper-driven checks."""

import ast
from pathlib import Path


def test_browser_lifecycles_belong_to_fixtures():
    root = Path(__file__).parents[2]
    offenders = []
    for directory in (root / "server/tests", root / "static/tests"):
        for path in directory.glob("test_*.py"):
            tree = ast.parse(path.read_text())
            for function in ast.walk(tree):
                if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                fixture = any(
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "fixture"
                    or isinstance(decorator, ast.Attribute)
                    and decorator.attr == "fixture"
                    for decorator in function.decorator_list
                )
                if fixture:
                    continue
                for call in ast.walk(function):
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
    assert not offenders, "Browser lifecycles outside fixtures: " + ", ".join(offenders)
