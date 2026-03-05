"""Tests for the /click endpoint – column pruning and sentinel behaviour.

Two bugs were fixed in this session:

  Bug 1 – Previewing a file in column N must close column N+1 and beyond.
           The response now embeds a JS loop that walks from col-{col}
           rightward, removing each element until it reaches #preview.

  Bug 2 – After the prune the col-{col} sentinel must be recreated so that
           directory links in column N (which target #col-{col} via HTMX
           outerHTML swap) remain valid.
"""

import pytest
from pathlib import Path
from starlette.testclient import TestClient

import pykofinder.app as app_module


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_root(tmp_path: Path):
    """Point app.ROOT at a minimal temp tree for the duration of the test."""
    (tmp_path / "subdir").mkdir()
    (tmp_path / "note.md").write_text("# Hello\n")
    original = app_module.ROOT
    app_module.ROOT = tmp_path
    yield tmp_path
    app_module.ROOT = original


@pytest.fixture()
def client(tmp_root):
    return TestClient(app_module.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Bug 1 – columns to the right of a file preview are pruned
# ---------------------------------------------------------------------------


def test_file_click_embeds_pruning_script(client, tmp_root):
    """Response for a file click must contain a <script> block."""
    path = tmp_root / "note.md"
    body = client.get(f"/click?path={path}&col=2").text
    assert "<script>" in body


def test_file_click_pruning_targets_correct_col(client, tmp_root):
    """The pruning loop must reference col-{col} (not a hard-coded id)."""
    path = tmp_root / "note.md"
    for col in (1, 2, 5):
        body = client.get(f"/click?path={path}&col={col}").text
        assert f"col-{col}" in body, f"pruning script missing col-{col}"


def test_file_click_pruning_stops_at_preview(client, tmp_root):
    """The loop condition must reference 'preview' so it never removes #preview."""
    path = tmp_root / "note.md"
    body = client.get(f"/click?path={path}&col=2").text
    assert "preview" in body


# ---------------------------------------------------------------------------
# Bug 2 – the col-{col} sentinel is recreated after pruning
# ---------------------------------------------------------------------------


def test_file_click_recreates_sentinel(client, tmp_root):
    """After pruning, the response must inject a new col-{col} sentinel div."""
    path = tmp_root / "note.md"
    body = client.get(f"/click?path={path}&col=2").text
    assert "sentinel.id = 'col-2'" in body
    assert "insertBefore(sentinel, preview)" in body


def test_sentinel_id_matches_col_param(client, tmp_root):
    """Sentinel id must reflect the exact col param, not a hard-coded number."""
    path = tmp_root / "note.md"
    for col in (1, 3, 7):
        body = client.get(f"/click?path={path}&col={col}").text
        assert f"sentinel.id = 'col-{col}'" in body, f"wrong sentinel for col={col}"


def test_dir_click_does_not_create_file_sentinel(client, tmp_root):
    """A directory click at col=1 must NOT recreate col-1 as a sentinel.

    It creates col-2 (the *next* slot) via the column's own prune_script –
    a different mechanism – so sentinel.id = 'col-1' must be absent.
    """
    path = tmp_root / "subdir"
    body = client.get(f"/click?path={path}&col=1").text
    assert "sentinel.id = 'col-1'" not in body
