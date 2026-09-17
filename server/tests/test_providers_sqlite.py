"""Tests for filemill.providers.sqlite – SQLiteProvider enumeration and row records."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from filemill.providers.sqlite import (
    ROW_ICON,
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


def test_list_entries_preserve_provider_order(single_schema_db, provider):
    assert all(e.ordered for e in provider.list_entries(single_schema_db, ""))
    assert all(e.ordered for e in provider.list_entries(single_schema_db, "users"))


def test_list_entries_table_icon(single_schema_db, provider):
    entries = provider.list_entries(single_schema_db, "")
    assert all(e.icon == TABLE_ICON for e in entries)


def test_list_entries_table_vpath_is_table_name(single_schema_db, provider):
    entries = provider.list_entries(single_schema_db, "")
    vpaths = {e.vpath for e in entries}
    assert "users" in vpaths
    assert "orders" in vpaths


def test_quoted_table_and_column_names_are_supported(tmp_path, provider):
    db = tmp_path / "quoted.db"
    con = sqlite3.connect(str(db))
    con.execute('CREATE TABLE "user""s" ("id""x" INTEGER PRIMARY KEY)')
    con.execute('INSERT INTO "user""s" VALUES (1)')
    con.commit()
    con.close()

    entries = provider.list_entries(db, 'user"s')
    assert entries[0].vpath == 'user"s/1'
    assert entries[0].record == {'id"x': 1}


def test_injection_shaped_identifier_cannot_escape_quoting(single_schema_db, provider):
    assert provider.list_entries(single_schema_db, 'users"; DROP TABLE users;--') == []
    assert provider.list_entries(single_schema_db, 'users/1" OR 1=1--') == []
    assert provider.list_entries(single_schema_db, "")


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


# ── list_entries – row records ────────────────────────────────────────────────


def test_table_entries_carry_no_record(single_schema_db, provider):
    assert all(e.record is None for e in provider.list_entries(single_schema_db, ""))


def test_row_entry_carries_its_cells_as_a_record(single_schema_db, provider):
    entries = provider.list_entries(single_schema_db, "users")
    assert entries[0].record == {"id": 1, "name": "Alice"}
    assert entries[1].record == {"id": 2, "name": "Bob"}


def test_record_excludes_the_rowid_alias(tmp_path, provider):
    db = tmp_path / "norowid.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (a TEXT, b TEXT)")
    con.execute("INSERT INTO t VALUES ('x', 'y')")
    con.commit()
    con.close()
    assert provider.list_entries(db, "t")[0].record == {"a": "x", "b": "y"}


def test_record_null_cell_is_none(tmp_path, provider):
    db = tmp_path / "null.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, note TEXT)")
    con.execute("INSERT INTO t VALUES (1, NULL)")
    con.commit()
    con.close()
    assert provider.list_entries(db, "t")[0].record == {"id": 1, "note": None}


def test_record_blob_cell_becomes_a_binary_note(tmp_path, provider):
    db = tmp_path / "blob2.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, data BLOB)")
    con.execute("INSERT INTO t VALUES (1, ?)", (b"\x00\x01\x02",))
    con.commit()
    con.close()
    record = provider.list_entries(db, "t")[0].record
    assert record == {"id": 1, "data": "⟨binary data, 3 bytes⟩"}


def test_record_long_string_is_not_truncated(tmp_path, provider):
    db = tmp_path / "long.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, note TEXT)")
    con.execute("INSERT INTO t VALUES (1, ?)", ("x" * 300,))
    con.commit()
    con.close()
    assert provider.list_entries(db, "t")[0].record == {"id": 1, "note": "x" * 300}


def test_provider_has_no_html_renderer(provider):
    assert not hasattr(provider, "render_preview")
    assert not hasattr(provider, "default_fmt")
