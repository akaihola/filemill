# Milestone 08 – VFS providers

The VFS protocol from Milestone 3 and the dispatch code in the app routes
have been waiting for concrete providers. This milestone delivers three:
a full-featured **SQLite** provider that lets you browse database tables
and rows as columns, a **JSON** provider that renders prettified,
syntax-highlighted JSON, and a **CSV** stub reserved for future expansion.

## Activating provider registration

In Milestone 3 we left a stub at the bottom of `vfs.py` where provider
imports belong. Now we replace it with the real imports. Each provider
module calls `REGISTRY.register(...)` at import time, so merely importing
the module activates it.

```python "vfs provider imports"
# ── Provider registration (side-effects) ──────────────────────────────────────
# These imports MUST remain at the bottom, after all names above are defined.
# Each provider module does `REGISTRY.register(...)` at import time.
from pykofinder.providers import sqlite  # noqa: E402, F401
from pykofinder.providers import csv_provider  # noqa: E402, F401
from pykofinder.providers import json_provider  # noqa: E402, F401
```

## SQLite provider

The SQLite provider is the most complex. It maps the database's
internal structure to a navigable column tree:

| Depth | What you see                                    | VFS concept  |
| ----- | ----------------------------------------------- | ------------ |
| 0     | Table list (or schema list if multiple schemas) | Folders      |
| 1     | Row listing for a table (max 500 entries)       | Leaf entries |
| 2     | Key-value detail for a single row               | Preview      |

The provider also offers a **spreadsheet** format where clicking a table
shows the full `<table>` with sticky headers, pagination, and a toggle
bar to switch back to the column (rows) view.

### Module setup and helpers

```python src/pykofinder/providers/sqlite.py
"""SQLite VFS provider for pykofinder.

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

from pykofinder.vfs import REGISTRY, VFSEntry, _truncate

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
```

### Provider class and protocol methods

The class opens the database in read-only mode (`?mode=ro`) for every
operation to avoid accidental writes.

```python src/pykofinder/providers/sqlite.py +=


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
```

### Entry listing

The inner listing method examines the `vpath` depth to decide what to
show: schemas at depth 0 (when multiple schemas exist), tables at
depth 0 or 1, and rows deeper down.

```python src/pykofinder/providers/sqlite.py +=

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
            )
            for row in rows
        ]
```

### Row listing and key derivation

Rows are identified by a display key derived from the table's primary
key, or – when no PK exists – by the rowid. A clever heuristic checks
whether the first column contains unique values and uses it as the
display label if so.

```python src/pykofinder/providers/sqlite.py +=

    # ── Row listing ───────────────────────────────────────────────────────────

    def _list_rows(
        self,
        con: sqlite3.Connection,
        schema: str,
        table: str,
        parent_vpath: str,
    ) -> list[VFSEntry]:
        rows = con.execute(
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
                )
            )
        if len(rows) == MAX_ROW_ENTRIES:
            entries.append(
                VFSEntry(
                    name=f"(first {MAX_ROW_ENTRIES} shown)",
                    vpath="",
                    is_folder=False,
                    icon="ℹ️",
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

        # Fallback: use _rowid_ alias
        try:
            rowid = row["_rowid_"]
            return f"row_{rowid}"
        except (IndexError, KeyError):
            return f"row_{idx + 1}"
```

### Preview rendering

The provider renders two formats: a paginated spreadsheet with sticky
headers, and a key-value detail view for individual rows.

```python src/pykofinder/providers/sqlite.py +=

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
```

### Spreadsheet renderer

The spreadsheet view shows a paginated HTML `<table>` with column names
as sticky headers. Navigation between pages uses HTMX links that target
`#preview`. A format-toggle bar lets the user switch back to row mode.

```python src/pykofinder/providers/sqlite.py +=

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

        # Format-toggle bar
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
```

### Key-value row detail

When the user clicks a specific row entry, this renderer shows every
column as a label-value pair in a two-column table.

```python src/pykofinder/providers/sqlite.py +=

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
```

## CSV provider (stub)

The CSV provider is reserved for future implementation. For now it
claims `.csv` files (preventing them from being shown as raw text) and
returns a placeholder message.

```python src/pykofinder/providers/csv_provider.py
"""CSV VFS provider stub for pykofinder."""

from __future__ import annotations

from pathlib import Path

from pykofinder.vfs import REGISTRY, VFSEntry


class CSVProvider:
    """Stub VFS provider for .csv files (spreadsheet vs raw, not yet implemented)."""

    def handles(self, path: Path) -> bool:
        return path.suffix.lower() == ".csv"

    def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]:
        return []

    def render_preview(
        self,
        path: Path,
        vpath: str,
        fmt: str,
        page: int,
        limit: int,
        col: int = 0,
    ) -> str:
        return (
            '<div class="preview-unsupported">'
            "<em>CSV VFS not yet implemented.</em></div>"
        )

    def default_fmt(self, vpath: str) -> str:
        return "spreadsheet"


REGISTRY.register(CSVProvider())
```

## JSON provider

The JSON provider renders any `.json` file as prettified,
syntax-highlighted JSON. It has no navigable children – the file is
always a leaf – so `list_entries` returns an empty list.

```python src/pykofinder/providers/json_provider.py
"""JSON VFS provider for pykofinder."""

from __future__ import annotations

import html as html_lib
import json as json_module
from pathlib import Path

from pykofinder.vfs import REGISTRY, VFSEntry


class JSONProvider:
    """VFS provider for .json files – renders formatted JSON with syntax highlighting."""

    def handles(self, path: Path) -> bool:
        return path.suffix.lower() == ".json"

    def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]:
        return []

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
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return '<div class="preview-unsupported"><em>Cannot read file as UTF-8.</em></div>'

        # Pretty-print if valid JSON; fall back to raw text if malformed
        try:
            data = json_module.loads(text)
            pretty = json_module.dumps(data, indent=2, ensure_ascii=False)
        except json_module.JSONDecodeError:
            pretty = text

        # Pygments syntax highlighting for JSON
        try:
            from pygments import highlight as pyg_highlight
            from pygments.formatters import HtmlFormatter as PygHtmlFormatter
            from pygments.lexers import get_lexer_by_name

            lexer = get_lexer_by_name("json")
            formatter = PygHtmlFormatter(style="friendly", nowrap=False)
            highlighted = pyg_highlight(pretty, lexer, formatter)
            return f'<div class="preview-code">{highlighted}</div>'
        except Exception:
            return f'<pre class="preview-raw">{html_lib.escape(pretty)}</pre>'

    def default_fmt(self, vpath: str) -> str:
        return "formatted"


REGISTRY.register(JSONProvider())
```

## Verification

```bash
rm -rf _tangle_out && mkdir _tangle_out && cd _tangle_out
lmt ../01-*.md ../02-*.md ../03-*.md ../04-*.md ../05-*.md ../06-*.md ../07-*.md ../08-*.md
uv sync
python -c "
from pykofinder.vfs import REGISTRY
print('Registered providers:', len(REGISTRY._providers))
for p in REGISTRY._providers:
    print(f'  {type(p).__name__}')
"
```

You should see three registered providers: `SQLiteProvider`, `CSVProvider`,
and `JSONProvider`.
