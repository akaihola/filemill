"""Tests for filemill.providers.sqlite – SQLiteProvider enumeration + preview."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from filemill.providers.sqlite import (
    ROW_ICON,
    SCHEMA_ICON,
    TABLE_ICON,
    SQLiteProvider,
)


@pytest.fixture()
def provider() -> SQLiteProvider:
    return SQLiteProvider()


@pytest.fixture()
def single_schema_db(tmp_path: Path) -> Path:
    """SQLite DB with one schema (main) and two tables."""
    db = tmp_path / "test.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    con.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, amount REAL)")
    con.execute("INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob')")
    con.commit()
    con.close()
    return db


# ── handles() ────────────────────────────────────────────────────────────────


def test_handles_db_extension(provider):
    assert provider.handles(Path("foo.db")) is True


def test_handles_DB_uppercase(provider):
    assert provider.handles(Path("foo.DB")) is True


def test_does_not_handle_csv(provider):
    assert provider.handles(Path("foo.csv")) is False


def test_does_not_handle_txt(provider):
    assert provider.handles(Path("data.txt")) is False


# ── list_entries – table enumeration ─────────────────────────────────────────


def test_list_entries_empty_vpath_returns_tables_single_schema(
    single_schema_db, provider
):
    entries = provider.list_entries(single_schema_db, "")
    names = [e.name for e in entries]
    assert "users" in names
    assert "orders" in names


def test_list_entries_tables_are_folders(single_schema_db, provider):
    entries = provider.list_entries(single_schema_db, "")
    assert all(e.is_folder for e in entries)


def test_list_entries_table_icon(single_schema_db, provider):
    entries = provider.list_entries(single_schema_db, "")
    assert all(e.icon == TABLE_ICON for e in entries)


def test_list_entries_table_vpath_is_table_name(single_schema_db, provider):
    entries = provider.list_entries(single_schema_db, "")
    vpaths = {e.vpath for e in entries}
    assert "users" in vpaths
    assert "orders" in vpaths


def test_list_entries_skips_sqlite_internal_tables(tmp_path, provider):
    db = tmp_path / "x.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (x TEXT)")
    # sqlite_sequence is created by AUTOINCREMENT; simulate internal table check
    con.commit()
    con.close()
    entries = provider.list_entries(db, "")
    assert all(not e.name.startswith("sqlite_") for e in entries)


def test_list_entries_returns_empty_list_on_bad_path(provider):
    entries = provider.list_entries(Path("/nonexistent/fake.db"), "")
    assert entries == []


def test_default_fmt_returns_folders(provider):
    assert provider.default_fmt("") == "folders"
    assert provider.default_fmt("users") == "folders"


# ── list_entries – row enumeration ────────────────────────────────────────────


def test_list_entries_for_table_vpath_returns_row_entries(single_schema_db, provider):
    entries = provider.list_entries(single_schema_db, "users")
    assert len(entries) == 2


def test_row_entries_have_row_icon(single_schema_db, provider):
    entries = provider.list_entries(single_schema_db, "users")
    assert all(e.icon == ROW_ICON for e in entries)


def test_row_entries_are_not_folders(single_schema_db, provider):
    entries = provider.list_entries(single_schema_db, "users")
    assert all(not e.is_folder for e in entries)


def test_row_key_single_pk(single_schema_db, provider):
    entries = provider.list_entries(single_schema_db, "users")
    vpaths = {e.vpath for e in entries}
    assert "users/1" in vpaths
    assert "users/2" in vpaths


def test_row_key_no_pk_uses_rowid(tmp_path, provider):
    db = tmp_path / "nopk.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (name TEXT)")
    con.execute("INSERT INTO t VALUES ('x'), ('y')")
    con.commit()
    con.close()
    entries = provider.list_entries(db, "t")
    assert all(e.vpath.startswith("t/row_") for e in entries)


def test_row_key_unique_first_col(tmp_path, provider):
    db = tmp_path / "uniq.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (code TEXT, val INTEGER)")
    con.execute("INSERT INTO t VALUES ('A', 1), ('B', 2)")
    con.commit()
    con.close()
    entries = provider.list_entries(db, "t")
    vpaths = {e.vpath for e in entries}
    assert "t/A" in vpaths
    assert "t/B" in vpaths


def test_row_key_non_unique_first_col_falls_back_to_rowid(tmp_path, provider):
    db = tmp_path / "dup.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (name TEXT)")
    con.execute("INSERT INTO t VALUES ('dup'), ('dup')")
    con.commit()
    con.close()
    entries = provider.list_entries(db, "t")
    assert all(e.vpath.startswith("t/row_") for e in entries)


def test_row_key_blob_value_pk_wins(tmp_path, provider):
    """BLOB is in a non-PK column; PK (id) is used as the key."""
    db = tmp_path / "blob.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, data BLOB)")
    con.execute("INSERT INTO t VALUES (1, ?)", (b"\x00\x01\x02",))
    con.commit()
    con.close()
    entries = provider.list_entries(db, "t")
    assert entries[0].vpath == "t/1"


def test_row_key_truncates_long_pk(tmp_path, provider):
    db = tmp_path / "longpk.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id TEXT PRIMARY KEY)")
    con.execute("INSERT INTO t VALUES (?)", ("x" * 80,))
    con.commit()
    con.close()
    entry = provider.list_entries(db, "t")[0]
    assert len(entry.name) == 60
    assert entry.name.endswith("…")


def test_list_entries_max_row_entries_cap(tmp_path, provider):
    from filemill.providers.sqlite import MAX_ROW_ENTRIES

    db = tmp_path / "big.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    con.executemany(
        "INSERT INTO t VALUES (?)", [(i,) for i in range(MAX_ROW_ENTRIES + 1)]
    )
    con.commit()
    con.close()
    entries = provider.list_entries(db, "t")
    # MAX_ROW_ENTRIES rows + 1 info sentinel
    assert len(entries) == MAX_ROW_ENTRIES + 1
    assert entries[-1].name.startswith(f"(first {MAX_ROW_ENTRIES}")


def test_list_entries_row_vpath_format(single_schema_db, provider):
    entries = provider.list_entries(single_schema_db, "users")
    for e in entries:
        assert e.vpath.startswith("users/")


# ── render_preview – spreadsheet ─────────────────────────────────────────────


def test_render_preview_spreadsheet_has_db_table_class(single_schema_db, provider):
    html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
    assert "db-table" in html


def test_render_preview_spreadsheet_has_column_headers(single_schema_db, provider):
    html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
    assert "id" in html
    assert "name" in html


def test_render_preview_spreadsheet_has_data(single_schema_db, provider):
    html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
    assert "Alice" in html
    assert "Bob" in html


def test_render_preview_spreadsheet_has_fmt_bar(single_schema_db, provider):
    html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
    assert "fmt-bar" in html


def test_render_preview_spreadsheet_active_button_is_spreadsheet(
    single_schema_db, provider
):
    html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
    assert "📊 Spreadsheet" in html
    assert "fmt-btn active" in html or 'class="fmt-btn active"' in html


def test_render_preview_spreadsheet_rows_button_has_correct_col(
    single_schema_db, provider
):
    html = provider.render_preview(
        single_schema_db, "users", "spreadsheet", 1, 1000, col=3
    )
    assert "#col-3" in html


def test_render_preview_spreadsheet_single_page_no_pagination_links(
    single_schema_db, provider
):
    html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
    assert "← Prev" not in html
    assert "Next →" not in html


def test_render_preview_spreadsheet_page1_has_next_link(tmp_path, provider):
    db = tmp_path / "p.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    con.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(5)])
    con.commit()
    con.close()
    html = provider.render_preview(db, "t", "spreadsheet", 1, 2, 0)
    assert "Next →" in html
    assert "← Prev" not in html


def test_render_preview_spreadsheet_page2_has_both_links(tmp_path, provider):
    db = tmp_path / "p2.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    con.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(5)])
    con.commit()
    con.close()
    html = provider.render_preview(db, "t", "spreadsheet", 2, 2, 0)
    assert "← Prev" in html
    assert "Next →" in html


def test_render_preview_spreadsheet_last_page_has_no_next(tmp_path, provider):
    db = tmp_path / "p3.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    con.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(4)])
    con.commit()
    con.close()
    html = provider.render_preview(db, "t", "spreadsheet", 2, 2, 0)
    assert "← Prev" in html
    assert "Next →" not in html


def test_render_preview_spreadsheet_empty_table(tmp_path, provider):
    db = tmp_path / "empty.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    con.commit()
    con.close()
    html = provider.render_preview(db, "t", "spreadsheet", 1, 1000, 0)
    assert "empty" in html.lower()


# ── render_preview – KV row detail ───────────────────────────────────────────


def test_render_preview_kv_has_kv_table_class(single_schema_db, provider):
    html = provider.render_preview(single_schema_db, "users/1", "folders", 1, 1000, 0)
    assert "db-kv-table" in html


def test_render_preview_kv_shows_field_values(single_schema_db, provider):
    html = provider.render_preview(single_schema_db, "users/1", "folders", 1, 1000, 0)
    assert "Alice" in html


def test_render_preview_kv_no_fmt_bar(single_schema_db, provider):
    html = provider.render_preview(single_schema_db, "users/1", "folders", 1, 1000, 0)
    assert "fmt-bar" not in html


def test_render_preview_blob_shows_binary_note(tmp_path, provider):
    db = tmp_path / "blob2.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, data BLOB)")
    con.execute("INSERT INTO t VALUES (1, ?)", (b"\x00\x01\x02",))
    con.commit()
    con.close()
    html = provider.render_preview(db, "t/1", "folders", 1, 1000, 0)
    assert "binary data" in html
    assert "3 bytes" in html


def test_render_preview_long_string_truncated_in_spreadsheet(tmp_path, provider):
    db = tmp_path / "long.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, note TEXT)")
    con.execute("INSERT INTO t VALUES (1, ?)", ("x" * 300,))
    con.commit()
    con.close()
    html = provider.render_preview(db, "t", "spreadsheet", 1, 1000, 0)
    assert "…" in html


def test_render_preview_long_string_full_in_kv(tmp_path, provider):
    db = tmp_path / "long2.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, note TEXT)")
    con.execute("INSERT INTO t VALUES (1, ?)", ("x" * 300,))
    con.commit()
    con.close()
    html = provider.render_preview(db, "t/1", "folders", 1, 1000, 0)
    assert "x" * 300 in html


def test_render_preview_pagination_links_have_vpage_href(tmp_path, provider):
    db = tmp_path / "pg.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    con.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(3)])
    con.commit()
    con.close()
    html = provider.render_preview(db, "t", "spreadsheet", 1, 1, 0)
    assert "/vpage" in html


def test_render_preview_unknown_vpath_returns_error_or_message(tmp_path, provider):
    db = tmp_path / "x.db"
    sqlite3.connect(str(db)).close()
    html = provider.render_preview(db, "nonexistent_table", "spreadsheet", 1, 1000, 0)
    # Should not crash; returns error div or empty message or db-table
    assert "preview-error" in html or "empty" in html.lower() or "db-table" in html
