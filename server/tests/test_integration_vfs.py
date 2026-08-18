"""End-to-end VFS navigation tests via the HTTP layer."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import quote

import pytest
from starlette.testclient import TestClient

import filemill.app as app_module


@pytest.fixture()
def int_root(tmp_path: Path):
    db = tmp_path / "movies.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE films (id INTEGER PRIMARY KEY, title TEXT, year INTEGER)")
    for i in range(1, 12):  # 11 rows → pagination test with limit=5
        con.execute("INSERT INTO films VALUES (?, ?, ?)", (i, f"Film {i}", 2000 + i))
    con.commit()
    con.close()
    original = app_module.ROOT
    app_module.ROOT = tmp_path
    yield tmp_path
    app_module.ROOT = original


@pytest.fixture()
def int_client(int_root: Path):
    return TestClient(app_module.app, raise_server_exceptions=False)


@pytest.fixture()
def empty_table_root(tmp_path: Path):
    """tmp_root with a SQLite .db file that has an empty table."""
    db = tmp_path / "empty.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE slack_channels (id INTEGER PRIMARY KEY, name TEXT)")
    con.commit()
    con.close()
    original = app_module.ROOT
    app_module.ROOT = tmp_path
    yield tmp_path
    app_module.ROOT = original


@pytest.fixture()
def empty_table_client(empty_table_root: Path):
    return TestClient(app_module.app, raise_server_exceptions=False)


# ── Level 0: tables column ────────────────────────────────────────────────────


def test_db_navigation_level0_shows_tables_column(int_client, int_root):
    db = int_root / "movies.db"
    resp = int_client.get(f"/click?path={quote(str(db))}&col=1")
    assert resp.status_code == 200
    assert "films" in resp.text
    assert 'id="col-1"' in resp.text


# ── Level 1: row column (folders mode) ───────────────────────────────────────


def test_db_navigation_level1_folders_shows_row_column(int_client, int_root):
    db = int_root / "movies.db"
    resp = int_client.get(f"/click?path={quote(str(db))}&col=2&vpath=films&fmt=folders")
    assert resp.status_code == 200
    assert 'id="col-2"' in resp.text
    # Row entries: Film 1 has id=1 as PK key
    assert "1" in resp.text


# ── Level 1: spreadsheet mode ────────────────────────────────────────────────


def test_db_navigation_level1_spreadsheet_shows_preview(int_client, int_root):
    db = int_root / "movies.db"
    resp = int_client.get(
        f"/click?path={quote(str(db))}&col=2&vpath=films&fmt=spreadsheet"
    )
    assert resp.status_code == 200
    assert "db-table" in resp.text
    assert "Film 1" in resp.text
    # Sentinel for the column should be in the response (OOB or main)
    assert 'id="col-2"' in resp.text
    assert "hx-swap-oob" in resp.text


# ── Level 2: row KV detail ───────────────────────────────────────────────────


def test_db_navigation_level2_row_detail(int_client, int_root):
    db = int_root / "movies.db"
    # Row with id=1 → vpath=films/1
    resp = int_client.get(
        f"/click?path={quote(str(db))}&col=3&vpath={quote('films/1')}"
    )
    assert resp.status_code == 200
    assert "db-kv-table" in resp.text
    assert "Film 1" in resp.text


# ── /vpage pagination ─────────────────────────────────────────────────────────


def test_vpage_pagination_limit(int_client, int_root):
    db = int_root / "movies.db"
    r1 = int_client.get(f"/vpage?path={quote(str(db))}&vpath=films&page=1&limit=5")
    r3 = int_client.get(f"/vpage?path={quote(str(db))}&vpath=films&page=3&limit=5")
    assert "Film 1" in r1.text
    assert "Film 6" not in r1.text
    assert "Film 11" in r3.text


# ── Breadcrumb includes vpath segments ────────────────────────────────────────


def test_breadcrumb_shows_vpath_segments(int_client, int_root):
    db = int_root / "movies.db"
    resp = int_client.get(f"/click?path={quote(str(db))}&col=2&vpath=films&fmt=folders")
    assert "films" in resp.text


# ── Regression: existing real-FS navigation still works ──────────────────────


def test_existing_dir_navigation_still_works(int_client, int_root):
    resp = int_client.get(f"/click?path={quote(str(int_root))}&col=1")
    assert resp.status_code == 200
    # Should show movies.db in the column (VFS file, directory-like link)
    assert "movies" in resp.text


def test_existing_file_preview_still_works(int_client, int_root):
    md = int_root / "readme.md"
    md.write_text("# Hello")
    resp = int_client.get(f"/click?path={quote(str(md))}&col=1")
    assert resp.status_code == 200
    assert "Hello" in resp.text


# ── Regression #24: empty table must not corrupt the column layout ────────────


def test_empty_table_returns_sentinel_plus_oob_preview(
    empty_table_client, empty_table_root
):
    """Clicking an empty table must:
    - Return a col-N sentinel as the *main* swap target (outerHTML on #col-N)
    - Return the "Table is empty." preview via hx-swap-oob on #preview
    - NOT inject preview HTML as the innerHTML of a column slot.
    """
    db = empty_table_root / "empty.db"
    resp = empty_table_client.get(
        f"/click?path={quote(str(db))}&col=2&vpath=slack_channels"
    )
    assert resp.status_code == 200
    body = resp.text

    # Must carry the col-2 sentinel so HTMX can do the outerHTML swap
    assert 'id="col-2"' in body

    # Must carry an OOB preview update – not raw inline content
    assert 'hx-swap-oob="true"' in body
    assert 'id="preview"' in body

    # The "Table is empty." message must be in the OOB preview fragment
    assert "empty" in body.lower()

    # The preview fragment must NOT appear as a bare block of HTML
    # *before* the col-2 sentinel (which would mean it landed in the column slot)
    oob_idx = body.find('hx-swap-oob="true"')
    col_idx = body.find('id="col-2"')
    # col sentinel should appear first (or be the OOB-wrapped sentinel itself)
    assert col_idx < oob_idx or col_idx == 0


def test_empty_table_leaf_row_detail_still_works(empty_table_client, empty_table_root):
    """After the empty-table fix, true leaf (row detail) navigation still works."""
    # Use the int_root DB which has actual rows; just verify the interface is intact.
    pass  # covered by test_db_navigation_level2_row_detail above


def test_leaf_param_on_row_entries(empty_table_client, empty_table_root):
    """Row entry links in the column must carry leaf=1 in their hx-get URL."""
    # First get the table list (level 0)
    db = empty_table_root / "empty.db"
    # Add a row so the table has entries to list
    import sqlite3 as _sqlite3

    con = _sqlite3.connect(str(db))
    con.execute("INSERT INTO slack_channels VALUES (1, 'general')")
    con.commit()
    con.close()

    resp = empty_table_client.get(
        f"/click?path={quote(str(db))}&col=2&vpath=slack_channels"
    )
    assert resp.status_code == 200
    # Row entries must carry leaf=1 so the server knows the HTMX target is #preview
    assert "leaf=1" in resp.text
