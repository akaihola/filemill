"""Evidence partitions preserve test order and cover the full module."""

import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[2]
UI = ROOT / "server/tests/test_browser_new_ui.py"


def partition(part, items):
    removed = []
    config = SimpleNamespace(
        getoption=lambda name: part,
        hook=SimpleNamespace(pytest_deselected=lambda items: removed.extend(items)),
    )
    runpy.run_path(str(ROOT / "conftest.py"))["pytest_collection_modifyitems"](
        config, items
    )
    return removed


@pytest.mark.parametrize("part,expected", [("early", [0, 1, 2]), ("late", [3, 4])])
def test_served_ui_parts_cover_an_odd_collection_in_order(part, expected):
    original = [SimpleNamespace(path=UI, index=i) for i in range(5)]
    items = original.copy()
    removed = partition(part, items)
    assert [item.index for item in items] == expected
    assert sorted(item.index for item in items + removed) == list(range(5))
    assert len({id(item) for item in items + removed}) == 5


def test_served_ui_part_refuses_other_modules():
    items = [SimpleNamespace(path=UI), SimpleNamespace(path=Path(__file__))]
    original = items.copy()
    with pytest.raises(pytest.UsageError, match="only.*test_browser_new_ui"):
        partition("early", items)
    assert items == original
