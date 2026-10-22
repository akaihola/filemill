"""SQLite VFS provider for filemill.

Navigation levels:
  depth 0 (vpath=""):             list tables (skip schema level when only "main")
  depth 1 (vpath="table"):        list rows as leaf entries, each with its cells
"""

from __future__ import annotations

import sqlite3
from contextlib import suppress
from pathlib import Path

from filemill.vfs import REGISTRY, VFSEntry, _truncate

TABLE_ICON = "🗃️"
SCHEMA_ICON = "📁"
ROW_ICON = "📋"

MAX_ROW_ENTRIES = 500  # max rows shown in the folders/column view


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _json_val(v: object) -> object:
    """A cell as JSON: only bytes cannot travel as they are."""
    if isinstance(v, bytes):
        return f"⟨binary data, {len(v)} bytes⟩"
    return v


class SQLiteProvider:
    """VFS provider for SQLite .db files."""

    # ── Protocol: handles ─────────────────────────────────────────────────────

    def handles(self, path: Path) -> bool:
        return path.suffix.lower() == ".db"

    # ── Protocol: list_entries ────────────────────────────────────────────────

    def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]:
        try:
            con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            try:
                return self._list_entries_inner(con, vpath)
            finally:
                con.close()
        except Exception:
            return []

    def _list_entries_inner(
        self, con: sqlite3.Connection, vpath: str
    ) -> list[VFSEntry]:
        parts = [p for p in vpath.split("/") if p]

        # Determine schemas
        schemas = [
            row["name"] for row in con.execute("PRAGMA database_list").fetchall()
        ]
        non_main = [s for s in schemas if s != "main"]

        # depth 0 ─────────────────────────────────────────────────────────────
        if len(parts) == 0:
            if not non_main:
                # Single schema: list tables in main directly
                return self._list_tables(con, "main", prefix="")
            else:
                # Multiple schemas: list schema folders
                return [
                    VFSEntry(
                        name=_truncate(s),
                        vpath=s,
                        is_folder=True,
                        icon=SCHEMA_ICON,
                        ordered=True,
                    )
                    for s in schemas
                ]

        # depth 1 ─────────────────────────────────────────────────────────────
        if len(parts) == 1:
            candidate = parts[0]
            if non_main and candidate in schemas:
                # Multi-schema: list tables in this schema
                return self._list_tables(con, candidate, prefix=f"{candidate}/")
            else:
                # Single-schema: candidate is a table name → list rows
                return self._list_rows(con, "main", candidate, vpath)

        # depth 2 ─────────────────────────────────────────────────────────────
        if len(parts) == 2:
            schema_candidate, table_candidate = parts[0], parts[1]
            if non_main and schema_candidate in schemas:
                # Multi-schema: schema/table → list rows
                return self._list_rows(con, schema_candidate, table_candidate, vpath)
            else:
                # Single-schema table/rowkey is a leaf
                return []

        # depth ≥ 3: leaf
        return []

    # ── Table listing ─────────────────────────────────────────────────────────

    def _list_tables(
        self, con: sqlite3.Connection, schema: str, prefix: str
    ) -> list[VFSEntry]:
        rows = con.execute(
            f"SELECT name FROM {_quote_identifier(schema)}.sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()
        return [
            VFSEntry(
                name=_truncate(row["name"]),
                vpath=f"{prefix}{row['name']}",
                is_folder=True,
                icon=TABLE_ICON,
                ordered=True,
            )
            for row in rows
        ]

    # ── Row listing ───────────────────────────────────────────────────────────

    def _list_rows(
        self,
        con: sqlite3.Connection,
        schema: str,
        table: str,
        parent_vpath: str,
    ) -> list[VFSEntry]:
        rows = con.execute(
            # Use _rowid_ alias to avoid collision when INTEGER PRIMARY KEY
            # aliases the rowid (which makes 'rowid' vanish from column names).
            f"SELECT rowid AS _rowid_, * FROM {_quote_identifier(schema)}."
            f"{_quote_identifier(table)} "
            f"LIMIT {MAX_ROW_ENTRIES}"
        ).fetchall()
        pk_cols, first_col = self._key_columns(con, schema, table)
        entries: list[VFSEntry] = []
        for idx, row in enumerate(rows):
            key_str = _row_key(row, idx, pk_cols, first_col)
            entries.append(
                VFSEntry(
                    name=_truncate(key_str),
                    vpath=f"{parent_vpath}/{key_str}",
                    is_folder=False,
                    icon=ROW_ICON,
                    ordered=True,
                    record={
                        k: _json_val(v)
                        for k, v in zip(row.keys(), row, strict=True)
                        if k != "_rowid_"
                    },
                )
            )
        if len(rows) == MAX_ROW_ENTRIES:
            entries.append(
                VFSEntry(
                    name=f"(first {MAX_ROW_ENTRIES} shown)",
                    vpath="",
                    is_folder=False,
                    icon="ℹ️",
                    ordered=True,
                )
            )
        return entries

    # ── Row-key derivation ────────────────────────────────────────────────────

    def _key_columns(
        self, con: sqlite3.Connection, schema: str, table: str
    ) -> tuple[list[str], str | None]:
        """Primary-key columns in key order, and the first column if it is unique."""
        info = con.execute(
            f"PRAGMA {_quote_identifier(schema)}.table_info({_quote_identifier(table)})"
        ).fetchall()
        pk_cols = [
            col["name"]
            for col in sorted((c for c in info if c["pk"] > 0), key=lambda c: c["pk"])
        ]
        # Only probe the first column without a PK and when there are multiple
        # columns – single-column tables always use rowid so the label stays
        # stable even when values repeat later.
        if pk_cols or len(info) < 2:
            return pk_cols, None
        quoted = _quote_identifier(info[0]["name"])
        # Display-key probing is best effort; fall back to rowid on failure.
        with suppress(Exception):
            total, distinct = con.execute(
                f"SELECT COUNT(*), COUNT(DISTINCT {quoted}) FROM "
                f"(SELECT {quoted} FROM {_quote_identifier(schema)}."
                f"{_quote_identifier(table)} LIMIT {MAX_ROW_ENTRIES})"
            ).fetchone()
            if total == distinct > 0:
                return pk_cols, info[0]["name"]
        return pk_cols, None


def _key_val(v: object) -> str:
    return "NULL" if v is None else str(_json_val(v))


def _row_key(
    row: sqlite3.Row, idx: int, pk_cols: list[str], first_col: str | None
) -> str:
    """Derive a display key (priority: single-PK → composite-PK → unique-first-col → rowid)."""
    if len(pk_cols) == 1:
        with suppress(IndexError, KeyError):
            return _truncate(_key_val(row[pk_cols[0]]))
    elif pk_cols:
        parts = []
        for col in pk_cols:
            with suppress(IndexError, KeyError):
                parts.append(f"{col}={_key_val(row[col])}")
        if parts:
            return _truncate(", ".join(parts))
    if first_col is not None:
        with suppress(IndexError, KeyError):
            return _truncate(_key_val(row[first_col]))

    # Fallback: use _rowid_ alias (set by callers via SELECT rowid AS _rowid_, *)
    try:
        return f"row_{row['_rowid_']}"
    except (IndexError, KeyError):
        return f"row_{idx + 1}"


REGISTRY.register(SQLiteProvider())
