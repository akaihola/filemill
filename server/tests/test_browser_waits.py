"""Browser checks must wait for observable state instead of sleeping."""

from pathlib import Path


def test_browser_checks_use_condition_based_waits():
    root = Path(__file__).parents[2]
    paths = [*(root / "static").rglob("*.py"), *Path(__file__).parent.rglob("*.py")]
    fixed_wait = "_".join(("wait_for", "timeout"))  # noqa: FLY002 — avoid matching this guard
    offenders = [
        str(path.relative_to(root)) for path in paths if fixed_wait in path.read_text()
    ]
    assert not offenders, "Fixed browser waits: " + ", ".join(offenders)
