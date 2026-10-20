"""Keep the structural conditions repaired by issue 131 true."""

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]


def test_production_imports_are_at_module_level():
    nested = []
    for path in (ROOT / "server/src/filemill").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nested.extend(
                    f"{path.relative_to(ROOT)}:{child.lineno}"
                    for child in ast.walk(node)
                    if isinstance(child, (ast.Import, ast.ImportFrom))
                )
    assert not nested, nested


def test_rich_consent_decision_stays_under_forty_lines():
    path = next((ROOT / "docs/adr").glob("0036-*.md"))
    assert len(path.read_text().splitlines()) < 40


@pytest.mark.parametrize("module", ["model/state", "layout", "nav", "render"])
def test_ui_tuning_values_have_names_and_reasons(module):
    source = (ROOT / f"ui/core/{module}.js").read_text()
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    # Check the tuning values found by the older review, excluding prose.
    tuning = re.compile(r"(?<![\w.])(?:0\.5|1e-9|40|5000|1000|500|10|8)(?![\w.])")
    for line in source.splitlines():
        code, _, reason = line.partition("//")
        if tuning.search(code):
            assert re.match(r"const [A-Z_]+ = ", code), line
            assert reason.strip(), line
