"""SQLite VFS provider for filemill.

Navigation levels:
  depth 0 (vpath=""):             list tables (skip schema level when only "main")
  depth 1 (vpath="table"):        list rows as leaf entries  (folders mode default)
  depth 2 (vpath="table/rowkey"): row KV detail via render_preview
"""

from __future__ import annotations

import html as html_lib
import sqlite3
from pathlib import Path
from textwrap import dedent
from urllib.parse import quote as urlquote

from filemill.vfs import REGISTRY, VFSEntry, _truncate

TABLE_ICON = "🗃️"
SCHEMA_ICON = "📁"
ROW_ICON = "📋"

MAX_ROW_ENTRIES = 500  # max rows shown in the folders/column view
MAX_STR_LEN = 200  # strings longer than this are truncated in spreadsheet cells


def _cell_val(v: object) -> str:
    """Format a cell value for display in a spreadsheet (with truncation)."""
    if v is None:
        return ""
    if isinstance(v, bytes):
        return f"⟨binary data, {len(v)} bytes⟩"
    s = str(v)
    if len(s) > MAX_STR_LEN:
        return s[:MAX_STR_LEN] + "…"
    return s


def _full_val(v: object) -> str:
    """Format a cell value for KV detail (no string truncation)."""
    if v is None:
        return ""
    if isinstance(v, bytes):
        return f"⟨binary data, {len(v)} bytes⟩"
    return str(v)


class SQLiteProvider:
    """VFS provider for SQLite .db files."""

    # ── Protocol: handles ─────────────────────────────────────────────────────

    def handles(self, path: Path) -> bool:
        return path.suffix.lower() == ".db"

    # ── Protocol: default_fmt ─────────────────────────────────────────────────

    def default_fmt(self, vpath: str) -> str:
        return "folders"

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
            f"SELECT name FROM [{schema}].sqlite_master "  # noqa: S608
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
            f"SELECT rowid AS _rowid_, * FROM [{schema}].[{table}] "  # noqa: S608
            f"LIMIT {MAX_ROW_ENTRIES}"
        ).fetchall()
        entries: list[VFSEntry] = []
        for idx, row in enumerate(rows):
            key_str = self._row_key(con, schema, table, row, idx)
            entries.append(
                VFSEntry(
                    name=_truncate(key_str),
                    vpath=f"{parent_vpath}/{key_str}",
                    is_folder=False,
                    icon=ROW_ICON,
                    ordered=True,
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

    def _row_key(
        self,
        con: sqlite3.Connection,
        schema: str,
        table: str,
        row: sqlite3.Row,
        idx: int,
    ) -> str:
        """Derive a display key (priority: single-PK → composite-PK → unique-first-col → rowid)."""
        info = con.execute(
            f"PRAGMA [{schema}].table_info([{table}])"  # noqa: S608
        ).fetchall()

        pk_cols = sorted([col for col in info if col["pk"] > 0], key=lambda c: c["pk"])

        def _val(v: object) -> str:
            if isinstance(v, bytes):
                return f"⟨binary data, {len(v)} bytes⟩"
            return str(v) if v is not None else "NULL"

        if pk_cols:
            if len(pk_cols) == 1:
                col_name = pk_cols[0]["name"]
                try:
                    return _truncate(_val(row[col_name]))
                except (IndexError, KeyError):
                    pass
            else:
                parts = []
                for c in pk_cols:
                    try:
                        parts.append(f"{c['name']}={_val(row[c['name']])}")
                    except (IndexError, KeyError):
                        pass
                if parts:
                    return _truncate(", ".join(parts))

        # No PK (or PK lookup failed): check if first column is unique.
        # Only apply when there are multiple columns – single-column tables always
        # use rowid so the label stays stable even when values repeat later.
        if len(info) > 1:
            first_col = info[0]["name"]
            try:
                fetch_limit = MAX_ROW_ENTRIES
                total = con.execute(
                    f"SELECT COUNT(*) FROM (SELECT [{first_col}] "  # noqa: S608
                    f"FROM [{schema}].[{table}] LIMIT {fetch_limit})"
                ).fetchone()[0]
                distinct = con.execute(
                    f"SELECT COUNT(DISTINCT [{first_col}]) FROM "  # noqa: S608
                    f"(SELECT [{first_col}] FROM [{schema}].[{table}] LIMIT {fetch_limit})"
                ).fetchone()[0]
                if total == distinct and distinct > 0:
                    try:
                        return _truncate(_val(row[first_col]))
                    except (IndexError, KeyError):
                        pass
            except Exception:
                pass

        # Fallback: use _rowid_ alias (set by callers via SELECT rowid AS _rowid_, *)
        try:
            rowid = row["_rowid_"]
            return f"row_{rowid}"
        except (IndexError, KeyError):
            return f"row_{idx + 1}"

    # ── Protocol: render_preview ──────────────────────────────────────────────

    def render_preview(
        self,
        path: Path,
        vpath: str,
        fmt: str,
        page: int,
        limit: int,
        col: int = 0,
    ) -> str:
        try:
            con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            try:
                return self._render_inner(con, path, vpath, fmt, page, limit, col)
            finally:
                con.close()
        except Exception as exc:
            return (
                f'<div class="preview-error">'
                f"DB preview error: {html_lib.escape(str(exc))}</div>"
            )

    def _render_inner(
        self,
        con: sqlite3.Connection,
        path: Path,
        vpath: str,
        fmt: str,
        page: int,
        limit: int,
        col: int,
    ) -> str:
        parts = [p for p in vpath.split("/") if p]

        schemas = [
            row["name"] for row in con.execute("PRAGMA database_list").fetchall()
        ]
        non_main = [s for s in schemas if s != "main"]
        multi_schema = bool(non_main)

        if multi_schema:
            if len(parts) >= 3:
                schema, table = parts[0], parts[1]
                row_key = "/".join(parts[2:])
                return self._render_kv(con, schema, table, row_key)
            if len(parts) == 2:
                schema, table = parts[0], parts[1]
                return self._render_spreadsheet(
                    con, path, vpath, schema, table, page, limit, col
                )
        else:
            if len(parts) >= 2:
                table = parts[0]
                row_key = "/".join(parts[1:])
                return self._render_kv(con, "main", table, row_key)
            if len(parts) == 1:
                table = parts[0]
                return self._render_spreadsheet(
                    con, path, vpath, "main", table, page, limit, col
                )

        return (
            '<div class="preview-unsupported"><em>Select a table to preview.</em></div>'
        )

    # ── Spreadsheet renderer ──────────────────────────────────────────────────

    def _render_spreadsheet(
        self,
        con: sqlite3.Connection,
        path: Path,
        vpath: str,
        schema: str,
        table: str,
        page: int,
        limit: int,
        col: int,
    ) -> str:
        try:
            rows = con.execute(
                f"SELECT * FROM [{schema}].[{table}] LIMIT ? OFFSET ?",  # noqa: S608
                (limit, (page - 1) * limit),
            ).fetchall()
            total = con.execute(
                f"SELECT COUNT(*) FROM [{schema}].[{table}]"  # noqa: S608
            ).fetchone()[0]
        except Exception as exc:
            return (
                f'<div class="preview-error">'
                f"DB preview error: {html_lib.escape(str(exc))}</div>"
            )

        total_pages = max(1, -(-total // limit))  # ceiling division

        # Column names
        try:
            col_names = [
                desc[0]
                for desc in con.execute(
                    f"SELECT * FROM [{schema}].[{table}] LIMIT 0"  # noqa: S608
                ).description
                or []
            ]
        except Exception:
            col_names = list(rows[0].keys()) if rows else []

        th_cells = "".join(f"<th>{html_lib.escape(c)}</th>" for c in col_names)
        tr_rows = []
        for row in rows:
            cells = "".join(
                f"<td>{html_lib.escape(_cell_val(row[c]))}</td>" for c in col_names
            )
            tr_rows.append(f"<tr>{cells}</tr>")

        if total == 0:
            body = '<p style="padding:1rem;color:#666;">Table is empty.</p>'
        else:
            table_html = dedent(f"""\
                <table class="db-table">
                  <thead><tr>{th_cells}</tr></thead>
                  <tbody>{"".join(tr_rows)}</tbody>
                </table>""")
            body = f'<div class="db-table-wrap">{table_html}</div>'

        # Pagination controls
        encoded_path = urlquote(str(path))
        encoded_vpath = urlquote(vpath)
        prev_link = ""
        next_link = ""
        if page > 1:
            prev_link = (
                f'<a hx-get="/vpage?path={encoded_path}&vpath={encoded_vpath}'
                f'&page={page - 1}&limit={limit}" '
                f'hx-target="#preview" hx-swap="innerHTML">← Prev</a>'
            )
        page_info = f"Page {page} of {total_pages} ({total} rows)"
        if page < total_pages:
            next_link = (
                f'<a hx-get="/vpage?path={encoded_path}&vpath={encoded_vpath}'
                f'&page={page + 1}&limit={limit}" '
                f'hx-target="#preview" hx-swap="innerHTML">Next →</a>'
            )
        pagination_html = (
            f'<div class="db-pagination">{prev_link}'
            f"<span>{page_info}</span>{next_link}</div>"
        )

        # Format-toggle bar (in the preview header area)
        encoded_path_esc = html_lib.escape(str(path))
        encoded_vpath_esc = html_lib.escape(vpath)
        rows_btn = (
            f'<button class="fmt-btn"'
            f' data-fmt="folders"'
            f' data-fpath="{encoded_path_esc}"'
            f' data-vpath="{encoded_vpath_esc}"'
            f' data-ext=".db"'
            f' hx-get="/click?path={encoded_path}&vpath={encoded_vpath}'
            f'&col={col}&fmt=folders"'
            f' hx-target="#col-{col}" hx-swap="outerHTML">📋 Rows</button>'
        )
        spreadsheet_btn = '<button class="fmt-btn active">📊 Spreadsheet</button>'
        fmt_bar = f'<div class="fmt-bar">{rows_btn}{spreadsheet_btn}</div>'

        return dedent(f"""\
            <div class="preview-db-spreadsheet">
              {fmt_bar}
              {body}
              {pagination_html}
            </div>""")

    # ── KV row-detail renderer ────────────────────────────────────────────────

    def _render_kv(
        self,
        con: sqlite3.Connection,
        schema: str,
        table: str,
        row_key: str,
    ) -> str:
        # Try row_N pattern first (rowid-based lookup)
        row = None
        if row_key.startswith("row_"):
            try:
                rowid = int(row_key[4:])
                row = con.execute(
                    f"SELECT * FROM [{schema}].[{table}] WHERE rowid = ?",  # noqa: S608
                    (rowid,),
                ).fetchone()
            except (ValueError, Exception):
                pass

        if row is None:
            # PK-based: iterate rows and match by reconstructed display key.
            # Use _rowid_ alias to avoid column-name collision with INTEGER PRIMARY KEY.
            try:
                all_rows = con.execute(
                    f"SELECT rowid AS _rowid_, * FROM [{schema}].[{table}] "  # noqa: S608
                    f"LIMIT {MAX_ROW_ENTRIES}"
                ).fetchall()
                for idx, r in enumerate(all_rows):
                    candidate = self._row_key(con, schema, table, r, idx)
                    if candidate == row_key or _truncate(candidate) == row_key:
                        rowid = r["_rowid_"]
                        row = con.execute(
                            f"SELECT * FROM [{schema}].[{table}] WHERE rowid = ?",  # noqa: S608
                            (rowid,),
                        ).fetchone()
                        break
            except Exception:
                pass

        if row is None:
            return (
                f'<div class="preview-error">'
                f"Row not found: {html_lib.escape(row_key)}</div>"
            )

        try:
            col_names = list(row.keys())
        except Exception:
            col_names = []

        rows_html = []
        for col_name in col_names:
            try:
                v = row[col_name]
            except (IndexError, KeyError):
                v = None
            display = html_lib.escape(_full_val(v))
            rows_html.append(
                f"<tr><th>{html_lib.escape(col_name)}</th><td>{display}</td></tr>"
            )

        table_html = f'<table class="db-kv-table">{"".join(rows_html)}</table>'
        return f'<div class="preview-db-row">{table_html}</div>'


REGISTRY.register(SQLiteProvider())
