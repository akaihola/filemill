# Implementation Plan – Issue #18

# Virtual-FS navigation and view-format switching (SQLite + extensible registry)

> **For the coder:** this document is self-contained. Read it top-to-bottom before
> writing a single line of code. Every function signature, test name, HTML snippet,
> CSS rule, and JS block is spelled out. Follow the TDD order exactly
> (red → green → commit at each numbered step).

---

## 0 · Project orientation

```
src/pykofinder/
├── app.py          – FastHTML app, routes, _resolve_safe()
├── cli.py          – Typer CLI
├── columns.py      – Column HTML generation + pruning JS
├── preview.py      – Preview dispatcher (md / docx / pptx / pdf / img / raw)
├── rendering.py    – markdown-it-py instance
└── styles.py       – APP_CSS string + COLUMN_JS string + LIVE_RELOAD_JS string

tests/
├── conftest.py     – tmp_root fixture (populates temp dir, patches app.ROOT) + client
├── test_app.py     – route-level integration tests
├── test_columns.py – column HTML generation
├── test_preview.py – preview rendering
├── test_rendering.py
├── test_resolve_safe.py
└── test_cli.py
```

### Key invariants

- **TDD**: write a failing test first; never write production code without a red test.
- **`uv run pytest`** for all test runs. Wrap in `timeout 120` to catch hangs.
- **`dedent()`** for every multi-line string (import from `textwrap`).
- **Conventional commits** at every logical checkpoint.
- **`sqlite3`** is stdlib – no new runtime dependency for the SQLite provider.
- All existing tests must keep passing throughout.

### Existing patterns to follow

**HTMX swap pattern** (from `app.py /click`):

```python
# Directory click → new column as main body, OOB clears preview + updates BC
new_col = list_column(p, ROOT, col_index=col)
preview_clear = Div(id="preview", hx_swap_oob="true")
bc_oob = render_breadcrumb(p, ROOT).replace(
    '<nav id="breadcrumb">', '<nav id="breadcrumb" hx-swap-oob="true">'
)
return new_col, preview_clear, NotStr(bc_oob)
```

**Column prune JS** (from `list_column`): each column div embeds a `<script>` that
removes all sibling columns to its right before `#preview`, then ensures the next
sentinel exists.

**FastHTML HTML** is built with `Div`, `Ul`, `Li`, `A`, `NotStr`, `Script` from
`fasthtml.common`. Calling `repr()` or `.__html__()` on them serialises to HTML.

**TestClient** is Starlette's sync test client (`from starlette.testclient import
TestClient`). Use `client.get("/click?path=…&col=1")` pattern.

**`tmp_root` fixture** sets `app_module.ROOT = tmp_path` and restores it on teardown.
**`client` fixture** depends on `tmp_root` and returns a `TestClient`.

---

## 1 · Architecture overview

### New modules

| Path                                        | Purpose                                                                                                 |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `src/pykofinder/vfs.py`                     | `VFSEntry`, `VFSProvider` protocol, `VFSRegistry`, `REGISTRY` singleton, `is_vfs_file()`, `_truncate()` |
| `src/pykofinder/providers/__init__.py`      | Empty package marker                                                                                    |
| `src/pykofinder/providers/sqlite.py`        | `SQLiteProvider` – schemas/tables/rows + preview                                                        |
| `src/pykofinder/providers/csv_provider.py`  | `CSVProvider` stub                                                                                      |
| `src/pykofinder/providers/json_provider.py` | `JSONProvider` stub                                                                                     |

### Modified modules

| Module                      | Changes                                                                                                                                                                       |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/pykofinder/columns.py` | `list_vfs_column()` (new); `entry_icon()` adds `.db → 🗄️`; `list_column()` treats VFS files like directories (targets next col); `render_breadcrumb()` gains `vpath=""` param |
| `src/pykofinder/app.py`     | `/click` gains `vpath: str = ""`, `fmt: str = ""`; VFS dispatch block; `_make_bc_oob()` + `_build_prune_js()` helpers extracted; `/vpage` new route                           |
| `src/pykofinder/styles.py`  | CSS and JS additions                                                                                                                                                          |

### New test files

| Path                             | Contents                                          |
| -------------------------------- | ------------------------------------------------- |
| `tests/test_vfs.py`              | `VFSEntry`, `VFSRegistry`, `VFSProvider` protocol |
| `tests/test_providers_sqlite.py` | `SQLiteProvider` enumeration + preview            |
| `tests/test_integration_vfs.py`  | End-to-end navigation with real `.db`             |

---

## 2 · URL / request model

**`/click` params** (new params are optional, backward-compatible):

| Param   | Type  | Default | Meaning                                                  |
| ------- | ----- | ------- | -------------------------------------------------------- |
| `path`  | `str` | –       | Real filesystem path (unchanged)                         |
| `col`   | `int` | –       | Column index (unchanged)                                 |
| `vpath` | `str` | `""`    | Virtual path within the file, e.g. `users` or `users/42` |
| `fmt`   | `str` | `""`    | View format override; empty → provider default           |

**`/vpage` params** (new endpoint):

| Param   | Type  | Default | Meaning                                   |
| ------- | ----- | ------- | ----------------------------------------- |
| `path`  | `str` | –       | Real filesystem path                      |
| `vpath` | `str` | –       | Virtual path (must be a table-level path) |
| `page`  | `int` | `1`     | 1-indexed page number                     |
| `limit` | `int` | `1000`  | Rows per page                             |

### HTMX swap strategy for VFS navigation

All VFS-level links (table entries, row entries, toggle buttons) use:

```
hx-target="#col-{col}"   hx-swap="outerHTML"
```

where `col` is the column the VFS node should occupy. The response's main body
replaces the `#col-{col}` element. OOB swaps handle preview and breadcrumb.

This means:

- **Clicking `.db` file** in `list_column` (real FS): link targets `#col-{next_col}`;
  response is the tables column (a real `<div id="col-N" …>`).
- **Clicking a table** (in VFS col), `fmt=folders`: response is the rows column
  - OOB clear preview.
- **Clicking a table** (in VFS col), `fmt=spreadsheet`: response is an empty sentinel
  `<div id="col-N"></div>` + OOB preview with spreadsheet HTML.
- **"📊 Spreadsheet" toggle** in column header: same as clicking the table with
  `fmt=spreadsheet` (self-targets `#col-{this_col}`, replaces itself with sentinel +
  OOB spreadsheet).
- **"📋 Rows" toggle** in preview header: targets `#col-{col}` where `col` is threaded
  through `render_preview`; response is rows column + OOB clear preview.
- **Clicking a row** in the rows column: link targets `#preview` with
  `hx-swap="innerHTML"` (leaf, never opens a new column).

### Format persistence (localStorage, client-side)

Two-tier lookup, resolved by JS before each HTMX request:

```
key vfmt_file_{raw_path}::{vpath}   →  most specific (per-file + vpath)
key vfmt_type_{.ext}                →  type-level fallback
built-in default (provider)         →  .db → "folders"; .csv → "spreadsheet"; .json → "formatted"
```

The JS reads from localStorage and injects `&fmt=…` only for links that have a
`data-fpath` attribute. Toggle buttons write to localStorage when clicked (before
HTMX fires the request).

---

## 3 · Full module specs

### 3.1 `src/pykofinder/vfs.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

MAX_LABEL_LEN = 60


def _truncate(s: str, n: int = MAX_LABEL_LEN) -> str:
    """Return s truncated to n chars with a trailing ellipsis if longer."""
    return s if len(s) <= n else s[: n - 1] + "…"


@dataclass
class VFSEntry:
    name: str       # display label, already truncated to MAX_LABEL_LEN chars
    vpath: str      # full virtual path key, e.g. "users" or "users/42"
    is_folder: bool # True → opens a new column on click; False → updates preview
    icon: str       # emoji


@runtime_checkable
class VFSProvider(Protocol):
    def handles(self, path: Path) -> bool: ...
    def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]: ...
    def render_preview(
        self,
        path: Path,
        vpath: str,
        fmt: str,
        page: int,
        limit: int,
        col: int = 0,
    ) -> str: ...
    def default_fmt(self, vpath: str) -> str: ...


class VFSRegistry:
    def __init__(self) -> None:
        self._providers: list[VFSProvider] = []

    def register(self, provider: VFSProvider) -> None:
        self._providers.append(provider)

    def get(self, path: Path) -> VFSProvider | None:
        """Return the last-registered provider that handles path, or None."""
        for p in reversed(self._providers):
            if p.handles(path):
                return p
        return None


REGISTRY = VFSRegistry()


def is_vfs_file(path: Path) -> bool:
    """True when path has a registered VFS provider (suffix-based check)."""
    return REGISTRY.get(path) is not None


# ── Trigger provider registration side-effects ────────────────────────────────
# These imports must remain at the bottom, after all names above are defined.
# Providers import VFSEntry / REGISTRY / _truncate from this module (already bound).
from pykofinder.providers import sqlite        # noqa: E402, F401
from pykofinder.providers import csv_provider  # noqa: E402, F401
from pykofinder.providers import json_provider # noqa: E402, F401
```

> **Circular-import safety:** `providers/sqlite.py` imports only from the _top_ of
> `vfs.py` (`VFSEntry`, `REGISTRY`, `_truncate`) – all defined before the bottom
> import block. Python caches partially-constructed modules in `sys.modules`, so
> when the provider does `from pykofinder.vfs import VFSEntry` mid-execution, it
> gets the already-bound names. No `ImportError` will occur.
>
> If in practice this causes problems, move the three bottom imports into a
> `_register_providers()` function and call it lazily from `REGISTRY.get()` on
> first invocation (guarded by a `_registered: bool` flag).

---

### 3.2 `src/pykofinder/providers/__init__.py`

Empty file.

---

### 3.3 `src/pykofinder/providers/sqlite.py`

```python
from __future__ import annotations
import html as html_lib
import sqlite3
from pathlib import Path
from textwrap import dedent
from urllib.parse import quote as urlquote

from pykofinder.vfs import VFSEntry, REGISTRY, _truncate

TABLE_ICON = "🗃️"
SCHEMA_ICON = "📁"
ROW_ICON    = "📋"

MAX_ROW_ENTRIES = 500   # max rows shown in the folders/column view
MAX_STR_LEN     = 200   # strings longer than this are truncated in spreadsheet cells
```

#### `SQLiteProvider.handles`

```python
def handles(self, path: Path) -> bool:
    return path.suffix.lower() == ".db"
```

#### `SQLiteProvider.default_fmt`

```python
def default_fmt(self, vpath: str) -> str:
    return "folders"   # always; table-level fmt is resolved per user preference
```

> **Note:** `has_format_toggle` was considered but removed from the protocol.
> The `/click` handler determines whether to show the format toggle by checking
> whether any returned entry has `icon == "📋"` (ROW_ICON):
>
> ```python
> show_fmt_bar = any(e.icon == "📋" for e in entries)
> ```
>
> This avoids a redundant DB round-trip and keeps the protocol minimal.

#### `SQLiteProvider.list_entries`

```python
def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]:
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        try:
            return self._list_entries_inner(con, path, vpath)
        finally:
            con.close()
    except Exception:
        return []
```

Private inner method:

```python
def _list_entries_inner(
    self, con: sqlite3.Connection, path: Path, vpath: str
) -> list[VFSEntry]:
    parts = [p for p in vpath.split("/") if p]

    # ── depth 0: determine if single-schema or multi-schema ──────────────────
    if len(parts) == 0:
        schemas = [
            row["name"]
            for row in con.execute("PRAGMA database_list").fetchall()
        ]
        non_main = [s for s in schemas if s != "main"]
        if not non_main:
            # Single schema: list tables directly
            return self._list_tables(con, "main")
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

    # ── depth 1 ───────────────────────────────────────────────────────────────
    if len(parts) == 1:
        # Could be: (a) single-schema table name → list rows
        #           (b) multi-schema schema name → list tables in that schema
        candidate = parts[0]
        # Check if it's a known schema
        schemas = [
            row["name"]
            for row in con.execute("PRAGMA database_list").fetchall()
        ]
        if candidate in schemas and candidate != "main":
            # Multi-schema: list tables in this schema
            return self._list_tables(con, candidate)
        else:
            # Single-schema: candidate is a table name → list rows
            return self._list_rows(con, "main", candidate, vpath)

    # ── depth 2 ───────────────────────────────────────────────────────────────
    if len(parts) == 2:
        # Either: (a) multi-schema schema/table → list rows
        #         (b) single-schema table/rowkey → leaf (should have been caught earlier)
        schema_candidate, table_candidate = parts
        schemas = [
            row["name"]
            for row in con.execute("PRAGMA database_list").fetchall()
        ]
        if schema_candidate in schemas:
            # Multi-schema: schema/table → list rows
            return self._list_rows(con, schema_candidate, table_candidate, vpath)
        else:
            # single-schema table/rowkey is a leaf – no entries
            return []

    # depth ≥ 3: leaf
    return []
```

`_list_tables(con, schema)` helper:

```python
def _list_tables(
    self, con: sqlite3.Connection, schema: str
) -> list[VFSEntry]:
    rows = con.execute(
        f"SELECT name FROM [{schema}].sqlite_master "  # noqa: S608
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    ).fetchall()
    return [
        VFSEntry(
            name=_truncate(row["name"]),
            vpath=row["name"] if schema == "main" else f"{schema}/{row['name']}",
            is_folder=True,
            icon=TABLE_ICON,
        )
        for row in rows
    ]
```

`_list_rows(con, schema, table, parent_vpath)` helper:

```python
def _list_rows(
    self,
    con: sqlite3.Connection,
    schema: str,
    table: str,
    parent_vpath: str,
) -> list[VFSEntry]:
    rows = con.execute(
        f"SELECT rowid, * FROM [{schema}].[{table}] LIMIT {MAX_ROW_ENTRIES}"  # noqa: S608
    ).fetchall()
    entries: list[VFSEntry] = []
    for idx, row in enumerate(rows):
        key_str = self._row_key(con, schema, table, row, idx)
        entries.append(
            VFSEntry(
                name=_truncate(key_str),
                vpath=f"{parent_vpath}/{key_str}",
                is_folder=False,   # rows are leaves → target #preview
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
```

#### Row-key derivation

```python
def _row_key(
    self,
    con: sqlite3.Connection,
    schema: str,
    table: str,
    row: sqlite3.Row,
    idx: int,
) -> str:
    """Derive a display key for a row (priority: PK → unique first col → rowid)."""
    info = con.execute(
        f"PRAGMA [{schema}].table_info([{table}])"  # noqa: S608
    ).fetchall()

    pk_cols = sorted(
        [col for col in info if col["pk"] > 0], key=lambda c: c["pk"]
    )

    def _val(v) -> str:
        if isinstance(v, bytes):
            return f"⟨binary data, {len(v)} bytes⟩"
        return str(v)

    if pk_cols:
        if len(pk_cols) == 1:
            col_name = pk_cols[0]["name"]
            return _truncate(_val(row[col_name]))
        else:
            parts = [f"{c['name']}={_val(row[c['name']])}" for c in pk_cols]
            return _truncate(", ".join(parts))

    # No PK: check if first column is unique
    if info:
        first_col = info[0]["name"]
        try:
            total = con.execute(
                f"SELECT COUNT(*) FROM (SELECT [{first_col}] FROM [{schema}].[{table}] LIMIT {MAX_ROW_ENTRIES})"  # noqa: S608
            ).fetchone()[0]
            distinct = con.execute(
                f"SELECT COUNT(DISTINCT [{first_col}]) FROM (SELECT [{first_col}] FROM [{schema}].[{table}] LIMIT {MAX_ROW_ENTRIES})"  # noqa: S608
            ).fetchone()[0]
            if total == distinct and distinct > 0:
                return _truncate(_val(row[first_col]))
        except Exception:
            pass

    # Fallback: rowid
    try:
        rowid = row["rowid"]
        return f"row_{rowid}"
    except (IndexError, KeyError):
        return f"row_{idx + 1}"
```

#### `SQLiteProvider.render_preview`

```python
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
        return f'<div class="preview-error">DB preview error: {html_lib.escape(str(exc))}</div>'
```

Private inner method: determines whether vpath is a row-detail or table-level path:

```python
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

    # Detect layout: single-schema or multi-schema
    schemas = [
        row["name"]
        for row in con.execute("PRAGMA database_list").fetchall()
    ]
    multi_schema = bool([s for s in schemas if s != "main"])

    if multi_schema:
        # depth 3+ = row detail: schema/table/rowkey
        if len(parts) >= 3:
            schema, table = parts[0], parts[1]
            row_key = "/".join(parts[2:])
            return self._render_kv(con, schema, table, row_key)
        # depth 2 = table level: schema/table
        if len(parts) == 2:
            schema, table = parts[0], parts[1]
            return self._render_spreadsheet(con, path, vpath, schema, table, page, limit, col)
        # depth 0 or 1 → not a previewable level (shouldn't happen via normal nav)
        return '<div class="preview-unsupported"><em>Select a table to preview.</em></div>'
    else:
        # Single schema
        # depth 2+ = row detail: table/rowkey
        if len(parts) >= 2:
            table = parts[0]
            row_key = "/".join(parts[1:])
            return self._render_kv(con, "main", table, row_key)
        # depth 1 = table level: table
        if len(parts) == 1:
            table = parts[0]
            return self._render_spreadsheet(con, path, vpath, "main", table, page, limit, col)
        return '<div class="preview-unsupported"><em>Select a table to preview.</em></div>'
```

#### Spreadsheet renderer

```python
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
    offset = (page - 1) * limit
    rows = con.execute(
        f"SELECT * FROM [{schema}].[{table}] LIMIT ? OFFSET ?"  # noqa: S608
        , (limit, offset)
    ).fetchall()
    total = con.execute(
        f"SELECT COUNT(*) FROM [{schema}].[{table}]"  # noqa: S608
    ).fetchone()[0]
    total_pages = max(1, -(-total // limit))   # ceiling division

    col_names = [desc[0] for desc in con.execute(
        f"SELECT * FROM [{schema}].[{table}] LIMIT 0"  # noqa: S608
    ).description or []]

    # Build header row
    th_cells = "".join(
        f"<th>{html_lib.escape(c)}</th>" for c in col_names
    )
    # Build data rows
    tr_rows = []
    for row in rows:
        cells = []
        for v in row:
            cells.append(f"<td>{html_lib.escape(_cell_val(v))}</td>")
        tr_rows.append(f"<tr>{''.join(cells)}</tr>")

    table_html = dedent(f"""\
        <table class="db-table">
          <thead><tr>{th_cells}</tr></thead>
          <tbody>{''.join(tr_rows)}</tbody>
        </table>""")

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
        f'<span>{page_info}</span>{next_link}</div>'
    )

    # Format-toggle bar (in the preview header area)
    rows_btn = (
        f'<button class="fmt-btn"'
        f' data-fmt="folders"'
        f' data-fpath="{html_lib.escape(str(path))}"'
        f' data-vpath="{html_lib.escape(vpath)}"'
        f' data-ext=".db"'
        f' hx-get="/click?path={encoded_path}&vpath={encoded_vpath}'
        f'&col={col}&fmt=folders"'
        f' hx-target="#col-{col}" hx-swap="outerHTML">📋 Rows</button>'
    )
    spreadsheet_btn = '<button class="fmt-btn active">📊 Spreadsheet</button>'
    fmt_bar = f'<div class="fmt-bar">{rows_btn}{spreadsheet_btn}</div>'

    if not rows and total == 0:
        body = '<p style="padding:1rem;color:#666;">Table is empty.</p>'
    else:
        body = f'<div class="db-table-wrap">{table_html}</div>'

    return dedent(f"""\
        <div class="preview-db-spreadsheet">
          {fmt_bar}
          {body}
          {pagination_html}
        </div>""")
```

Helper for cell values:

```python
def _cell_val(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bytes):
        return f"⟨binary data, {len(v)} bytes⟩"
    s = str(v)
    if len(s) > MAX_STR_LEN:
        return s[:MAX_STR_LEN] + "…"
    return s
```

#### Row KV renderer

```python
def _render_kv(
    self,
    con: sqlite3.Connection,
    schema: str,
    table: str,
    row_key: str,
) -> str:
    # Find the row: try rowid first (row_N pattern), then PK lookup
    row = None
    if row_key.startswith("row_"):
        try:
            rowid = int(row_key[4:])
            row = con.execute(
                f"SELECT * FROM [{schema}].[{table}] WHERE rowid = ?"  # noqa: S608
                , (rowid,)
            ).fetchone()
        except (ValueError, Exception):
            pass

    if row is None:
        # PK-based lookup: fetch all and match by display key
        # (simpler than reconstructing the PK query from key_str)
        rows_iter = con.execute(
            f"SELECT rowid, * FROM [{schema}].[{table}] LIMIT {MAX_ROW_ENTRIES}"  # noqa: S608
        ).fetchall()
        con2 = con   # reuse same connection
        for idx, r in enumerate(rows_iter):
            candidate_key = self._row_key(con2, schema, table, r, idx)
            if candidate_key == row_key or _truncate(candidate_key) == row_key:
                row = r
                break

    if row is None:
        return f'<div class="preview-error">Row not found: {html_lib.escape(row_key)}</div>'

    col_names = [desc[0] for desc in con.execute(
        f"SELECT * FROM [{schema}].[{table}] LIMIT 0"  # noqa: S608
    ).description or []]

    rows_html = []
    for col_name in col_names:
        try:
            v = row[col_name]
        except (IndexError, KeyError):
            v = None
        if isinstance(v, bytes):
            display = f"⟨binary data, {len(v)} bytes⟩"
        else:
            display = html_lib.escape(str(v) if v is not None else "")
        rows_html.append(
            f"<tr><th>{html_lib.escape(col_name)}</th><td>{display}</td></tr>"
        )

    table_html = f'<table class="db-kv-table">{"".join(rows_html)}</table>'
    return f'<div class="preview-db-row">{table_html}</div>'
```

#### Registration (bottom of `providers/sqlite.py`)

```python
REGISTRY.register(SQLiteProvider())
```

---

### 3.4 `src/pykofinder/providers/csv_provider.py`

```python
from __future__ import annotations
from pathlib import Path
from pykofinder.vfs import VFSEntry, REGISTRY


class CSVProvider:
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

---

### 3.5 `src/pykofinder/providers/json_provider.py`

```python
from __future__ import annotations
from pathlib import Path
from pykofinder.vfs import VFSEntry, REGISTRY


class JSONProvider:
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
        return (
            '<div class="preview-unsupported">'
            "<em>JSON VFS not yet implemented.</em></div>"
        )

    def default_fmt(self, vpath: str) -> str:
        return "formatted"


REGISTRY.register(JSONProvider())
```

---

### 3.6 `src/pykofinder/columns.py` – changes

#### `entry_icon`: add `.db` before final `else`

```python
elif ext == ".db":
    return "🗄️"
```

#### `render_breadcrumb`: add `vpath` parameter

New signature:

```python
def render_breadcrumb(path: Path, root: Path, vpath: str = "") -> str:
```

After the existing `for seg in segments:` loop, append:

```python
if vpath:
    for vseg in vpath.split("/"):
        if vseg:
            parts.append('<span class="bc-sep">/</span>')
            parts.append(
                f'<span class="bc-seg bc-virtual">'
                f'{html_lib.escape(vseg)}</span>'
            )
```

#### `list_column`: treat VFS files like directories

Add import at the top of `columns.py`:

```python
from pykofinder.vfs import is_vfs_file
```

In the `for p in entries:` loop, replace the `else:` branch (currently "File: update
preview only") with:

```python
elif is_vfs_file(p):
    # VFS navigable file: opens as a column, not a preview
    li = Li(
        A(
            NotStr(f'<span class="icon">{icon}</span>'),
            p.name,
            href="#",
            hx_get=f"/click?path={encoded_path}&col={next_col}",
            hx_target=f"#col-{next_col}",
            hx_swap="outerHTML",
            title=p.name,
        ),
    )
else:
    # Regular file: update preview only
    li = Li(
        A(
            NotStr(f'<span class="icon">{icon}</span>'),
            p.name,
            href="#",
            hx_get=f"/click?path={encoded_path}&col={next_col}",
            hx_target="#preview",
            hx_swap="innerHTML",
            title=p.name,
        ),
    )
```

#### New function: `list_vfs_column`

```python
def list_vfs_column(
    entries: list,         # list[VFSEntry]
    fs_path_encoded: str,  # URL-quoted real filesystem path (for hx-get URLs)
    fs_path_raw: str,      # raw (unquoted) filesystem path (for data-fpath)
    vpath: str,            # vpath for this column level (for fmt-bar hx-get + data-vpath)
    col_index: int,
    show_fmt_bar: bool = False,
    active_fmt: str = "folders",
    ext: str = "",         # file extension e.g. ".db" (for data-ext + localStorage)
) -> object:
    """Return a FastHTML Div for a VFS column panel."""
    from pykofinder.vfs import VFSEntry  # local import to avoid top-level circular

    next_col = col_index + 1
    items = []

    for entry in entries:
        if not isinstance(entry, VFSEntry) or not entry.name:
            continue
        encoded_vpath = urlquote(entry.vpath) if entry.vpath else ""

        if entry.is_folder:
            a = A(
                NotStr(f'<span class="icon">{entry.icon}</span>'),
                entry.name,
                href="#",
                hx_get=(
                    f"/click?path={fs_path_encoded}"
                    f"&col={next_col}"
                    f"&vpath={encoded_vpath}"
                ),
                hx_target=f"#col-{next_col}",
                hx_swap="outerHTML",
                title=entry.name,
                **{
                    "data-fpath": fs_path_raw,
                    "data-vpath": entry.vpath,
                    "data-ext": ext,
                },
            )
        else:
            # Leaf node (row entry or info sentinel): updates preview
            a = A(
                NotStr(f'<span class="icon">{entry.icon}</span>'),
                entry.name,
                href="#",
                hx_get=(
                    f"/click?path={fs_path_encoded}"
                    f"&col={next_col}"
                    f"&vpath={encoded_vpath}"
                ) if entry.vpath else "#",
                hx_target="#preview",
                hx_swap="innerHTML",
                title=entry.name,
                **{
                    "data-fpath": fs_path_raw,
                    "data-vpath": entry.vpath,
                    "data-ext": ext,
                },
            )
        items.append(Li(a))

    # Fmt-bar (shown only at the row-listing level when folders mode is active)
    fmt_bar_html = ""
    if show_fmt_bar:
        encoded_vpath_bar = urlquote(vpath)
        spreadsheet_btn = (
            f'<button class="fmt-btn"'
            f' data-fmt="spreadsheet"'
            f' data-fpath="{html_lib.escape(fs_path_raw)}"'
            f' data-vpath="{html_lib.escape(vpath)}"'
            f' data-ext="{html_lib.escape(ext)}"'
            f' hx-get="/click?path={fs_path_encoded}'
            f'&vpath={encoded_vpath_bar}'
            f'&col={col_index}&fmt=spreadsheet"'
            f' hx-target="#col-{col_index}" hx-swap="outerHTML">'
            f'📊 Spreadsheet</button>'
        )
        rows_btn = '<button class="fmt-btn active">📋 Rows</button>'
        fmt_bar_html = f'<div class="fmt-bar col-header">{rows_btn}{spreadsheet_btn}</div>'

    # Prune script (same pattern as list_column)
    prune_script = Script(
        f"""
(function(){{
    var col = document.getElementById('col-{col_index}');
    if (!col) return;
    var next = col.nextElementSibling;
    while(next && next.id !== 'preview'){{
        var toRemove = next;
        next = next.nextElementSibling;
        toRemove.remove();
    }}
    if (!document.getElementById('col-{next_col}')){{
        var sentinel = document.createElement('div');
        sentinel.id = 'col-{next_col}';
        var preview = document.getElementById('preview');
        if (preview) preview.parentNode.insertBefore(sentinel, preview);
    }}
}})();
"""
    )

    return Div(
        NotStr(fmt_bar_html) if fmt_bar_html else "",
        Ul(*items),
        prune_script,
        id=f"col-{col_index}",
        cls="column",
    )
```

Note: `html_lib` must be imported at the top of `columns.py`:

```python
import html as html_lib
```

---

### 3.7 `src/pykofinder/app.py` – changes

#### Imports to add

```python
from pykofinder.vfs import REGISTRY
from pykofinder.columns import list_vfs_column
```

> **Note:** importing `REGISTRY` from `vfs` triggers the full provider registration
> chain (vfs.py bottom imports sqlite, csv, json providers). This is the correct
> moment for the side-effect.

#### Extract two private helpers (refactor, no behaviour change)

Extract from the existing `/click` handler:

```python
def _make_bc_oob(path: Path, vpath: str = "") -> str:
    """Return a breadcrumb <nav> string with hx-swap-oob="true"."""
    return render_breadcrumb(path, ROOT, vpath).replace(
        '<nav id="breadcrumb">', '<nav id="breadcrumb" hx-swap-oob="true">'
    )


def _build_prune_js(col: int) -> str:
    """Return a <script> that prunes sibling columns ≥ col and restores sentinel."""
    return dedent(f"""\
        <script>
        (function(){{
            var el = document.getElementById('col-{col}');
            while (el && el.id !== 'preview') {{
                var next = el.nextElementSibling;
                el.remove();
                el = next;
            }}
            var sentinel = document.createElement('div');
            sentinel.id = 'col-{col}';
            var preview = document.getElementById('preview');
            if (preview) preview.parentNode.insertBefore(sentinel, preview);
        }})();
        </script>""")
```

Add `from textwrap import dedent` to `app.py` imports.

#### Extended `/click` handler

The full revised `/click` function (replacing the existing one completely):

```python
@rt("/click")
def click(path: str, col: int, vpath: str = "", fmt: str = ""):
    p = _resolve_safe(path)
    if p is None:
        return Div(
            "Access denied.",
            id=f"col-{col}",
            cls="column",
            style="color:#c00; padding:1rem;",
        )

    # ── VFS dispatch ──────────────────────────────────────────────────────────
    provider = REGISTRY.get(p)
    if provider is not None:
        resolved_fmt = fmt or provider.default_fmt(vpath)
        entries = provider.list_entries(p, vpath)
        is_leaf = not any(e.is_folder for e in entries) and not any(
            e.vpath for e in entries
        )

        if resolved_fmt == "spreadsheet":
            # Spreadsheet mode: collapse column to sentinel, OOB-update preview
            try:
                preview_html = provider.render_preview(
                    p, vpath, "spreadsheet", page=1, limit=1000, col=col
                )
            except Exception as exc:
                preview_html = (
                    f'<div class="preview-error">'
                    f'Preview error: {html_lib.escape(str(exc))}</div>'
                )
            sentinel = Div(id=f"col-{col}")
            preview_oob = NotStr(
                f'<div id="preview" hx-swap-oob="true">{preview_html}</div>'
            )
            bc_oob = NotStr(_make_bc_oob(p, vpath))
            return sentinel, preview_oob, bc_oob

        elif not any(e.is_folder for e in entries):
            # Leaf node (row detail): update preview directly
            try:
                preview_html = provider.render_preview(
                    p, vpath, resolved_fmt, page=1, limit=1000, col=col
                )
            except Exception as exc:
                preview_html = (
                    f'<div class="preview-error">'
                    f'Preview error: {html_lib.escape(str(exc))}</div>'
                )
            bc_oob = NotStr(_make_bc_oob(p, vpath))
            prune_js = _build_prune_js(col)
            return NotStr(preview_html + prune_js + bc_oob)

        else:
            # Column mode: folders / row listing
            show_fmt_bar = any(e.icon == "📋" for e in entries)
            encoded_path = urlquote(str(p))
            new_col = list_vfs_column(
                entries=entries,
                fs_path_encoded=encoded_path,
                fs_path_raw=str(p),
                vpath=vpath,
                col_index=col,
                show_fmt_bar=show_fmt_bar,
                active_fmt=resolved_fmt,
                ext=p.suffix.lower(),
            )
            preview_clear = Div(id="preview", hx_swap_oob="true")
            bc_oob = NotStr(_make_bc_oob(p, vpath))
            return new_col, preview_clear, bc_oob

    # ── Real directory ────────────────────────────────────────────────────────
    if p.is_dir():
        bc_oob = render_breadcrumb(p, ROOT).replace(
            '<nav id="breadcrumb">', '<nav id="breadcrumb" hx-swap-oob="true">'
        )
        new_col = list_column(p, ROOT, col_index=col)
        preview_clear = Div(id="preview", hx_swap_oob="true")
        return new_col, preview_clear, NotStr(bc_oob)

    # ── Regular file preview ──────────────────────────────────────────────────
    try:
        preview_html = render_preview(p)
    except Exception as e:
        preview_html = (
            f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        )
    prune_js = _build_prune_js(col)
    bc_oob = render_breadcrumb(p, ROOT).replace(
        '<nav id="breadcrumb">', '<nav id="breadcrumb" hx-swap-oob="true">'
    )
    return NotStr(preview_html + prune_js + bc_oob)
```

> **Backward compatibility:** the existing directory and file branches are identical
> to the old code modulo the `_make_bc_oob`/`_build_prune_js` refactor. Keep the
> existing raw string substitution in the directory/file branches (don't use the
> helpers there in the first commit) to minimise diff risk – or use the helpers
> everywhere, but run the full test suite before committing.

#### New `/vpage` endpoint

```python
@rt("/vpage")
def vpage(path: str, vpath: str, page: int = 1, limit: int = 1000):
    p = _resolve_safe(path)
    if p is None or not p.is_file():
        return HTMLResponse("Not found", status_code=404)
    provider = REGISTRY.get(p)
    if provider is None:
        return HTMLResponse("Not found", status_code=404)
    try:
        html = provider.render_preview(
            p, vpath, fmt="spreadsheet", page=page, limit=limit, col=0
        )
    except Exception as exc:
        html = (
            f'<div class="preview-error">'
            f'Preview error: {html_lib.escape(str(exc))}</div>'
        )
    return NotStr(html)
```

---

### 3.8 `src/pykofinder/styles.py` – changes

#### CSS additions

Append the following block at the end of the `APP_CSS` string (before the closing
`"""`), after the Pygments section:

```css
/* ── VFS / format toggle ─────────────────────────────────────────────────── */
.fmt-bar {
  display: flex;
  gap: 4px;
  padding: 4px 8px;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
  flex-shrink: 0;
}
.fmt-btn {
  padding: 2px 8px;
  border: 1px solid #bbb;
  border-radius: 3px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
}
.fmt-btn.active {
  background: #0070c9;
  color: #fff;
  border-color: #0070c9;
  cursor: default;
}

/* Column flex layout (needed for col-header fmt-bar above the ul) */
.column {
  display: flex;
  flex-direction: column;
}
.column ul {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* DB spreadsheet preview */
.preview-db-spreadsheet {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
.db-table-wrap {
  flex: 1;
  overflow: auto;
  min-height: 0;
}
.db-table {
  border-collapse: collapse;
  font-size: 12px;
  width: 100%;
}
.db-table th {
  background: #f0f0f0;
  border: 1px solid #ddd;
  padding: 4px 8px;
  position: sticky;
  top: 0;
  z-index: 1;
  white-space: nowrap;
}
.db-table td {
  border: 1px solid #eee;
  padding: 4px 8px;
  white-space: nowrap;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* DB KV row detail */
.preview-db-row {
  padding: 1rem;
  overflow: auto;
  height: 100%;
  box-sizing: border-box;
}
.db-kv-table {
  border-collapse: collapse;
  width: 100%;
}
.db-kv-table th {
  text-align: left;
  padding: 4px 12px 4px 0;
  color: #666;
  font-weight: 600;
  white-space: nowrap;
  vertical-align: top;
  min-width: 120px;
}
.db-kv-table td {
  padding: 4px 0;
  word-break: break-word;
}

/* DB pagination bar */
.db-pagination {
  padding: 6px 8px;
  border-top: 1px solid #ddd;
  font-size: 12px;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
  color: #555;
}
.db-pagination a {
  color: #0070c9;
  text-decoration: none;
  cursor: pointer;
}

/* Virtual breadcrumb segments */
.bc-virtual {
  font-style: italic;
  color: #555;
}
```

> **CSS regression risk:** Adding `display: flex; flex-direction: column` to
> `.column` may break the existing column layout. The existing CSS has `.column`
> with `height: 100%; overflow-y: auto;`. After the change, the `overflow-y: auto`
> moves to `.column ul`. Run existing `test_list_column_*` tests and do a manual
> visual check. If regression: scope as `.column.vfs-column` and add the class only
> in `list_vfs_column`.

#### JS additions

Append the following block to `COLUMN_JS` (after the existing keyboard-navigation
IIFE, before the closing backtick if using template literals, or as a concatenated
string):

```javascript
// ── VFS format persistence ──────────────────────────────────────────────────
(function () {
  var FMTKEY_TYPE = function (ext) {
    return "vfmt_type_" + ext;
  };
  var FMTKEY_FILE = function (fpath, vpath) {
    return "vfmt_file_" + fpath + "::" + vpath;
  };

  // Inject stored fmt into every HTMX request that carries data-fpath
  document.body.addEventListener("htmx:configRequest", function (evt) {
    var elt = evt.detail.elt;
    var fpath = elt.dataset.fpath;
    var vpath = elt.dataset.vpath;
    var ext = elt.dataset.ext;
    // Only intercept VFS navigation links (those with data-fpath)
    if (fpath === undefined) return;
    // Don't override an explicit fmt already in the request params
    if (evt.detail.parameters && evt.detail.parameters.fmt) return;
    var stored =
      localStorage.getItem(
        FMTKEY_FILE(fpath, vpath !== undefined ? vpath : ""),
      ) || (ext ? localStorage.getItem(FMTKEY_TYPE(ext)) : null);
    if (stored) {
      evt.detail.parameters = evt.detail.parameters || {};
      evt.detail.parameters.fmt = stored;
    }
  });

  // Toggle buttons write to localStorage when clicked (HTMX fires the request)
  document.body.addEventListener("click", function (evt) {
    var btn = evt.target.closest(".fmt-btn[data-fmt]");
    if (!btn || btn.classList.contains("active")) return;
    var fpath = btn.dataset.fpath;
    var vpath = btn.dataset.vpath;
    var ext = btn.dataset.ext;
    var fmt = btn.dataset.fmt;
    if (fpath !== undefined && vpath !== undefined) {
      localStorage.setItem(FMTKEY_FILE(fpath, vpath), fmt);
    }
    if (ext) {
      localStorage.setItem(FMTKEY_TYPE(ext), fmt);
    }
    // HTMX fires the request via hx-get on the button element itself
  });
})();
```

---

## 4 · Step-by-step TDD implementation order

### Step 1 – Bookkeeping

In `ISSUES.md`: change `**Status:** open` to `**Status:** in-progress` for `#18`.

In `TASKS.md`: move `[ ] #18 …` to the **In progress** section as `[~] #18 …`.

```
git commit -m "docs: mark issue #18 in-progress"
```

---

### Step 2 – Red: `tests/test_vfs.py`

Create the file. All tests must **fail** (module not yet created). Run to confirm:

```bash
timeout 120 uv run pytest tests/test_vfs.py -v 2>&1 | head -40
```

Tests:

```python
# test_truncate_short_string_unchanged
#   _truncate("hello") == "hello"

# test_truncate_long_string_at_60_chars
#   s = "x" * 70; result = _truncate(s); len(result) == 60; result.endswith("…")

# test_truncate_exactly_60_unchanged
#   _truncate("x" * 60) == "x" * 60

# test_vfs_entry_fields
#   e = VFSEntry(name="users", vpath="users", is_folder=True, icon="📁")
#   e.name == "users"; e.is_folder is True

# test_vfs_registry_get_returns_none_when_empty
#   reg = VFSRegistry(); reg.get(Path("foo.db")) is None

# test_vfs_registry_register_and_get_returns_provider
#   Create a FakeProvider class that handles ".db"; register it;
#   assert reg.get(Path("foo.db")) is that provider

# test_vfs_registry_get_returns_none_for_unmatched
#   reg = VFSRegistry(); register FakeProvider (handles ".db")
#   reg.get(Path("foo.csv")) is None

# test_vfs_registry_last_registered_wins
#   Register two providers that both handle ".db";
#   assert reg.get(Path("x.db")) is the second one

# test_vfs_provider_protocol_is_runtime_checkable
#   FakeProvider must implement all four methods: handles, list_entries,
#   render_preview, default_fmt (matching the Protocol signatures exactly)
#   assert isinstance(FakeProvider(), VFSProvider)

# test_is_vfs_file_returns_true_for_db(tmp_path)
#   f = tmp_path / "data.db"; f.touch()
#   from pykofinder.vfs import is_vfs_file
#   assert is_vfs_file(f) is True
#   (this test imports vfs which triggers provider registration)

# test_is_vfs_file_returns_false_for_txt(tmp_path)
#   f = tmp_path / "data.txt"; f.touch()
#   assert is_vfs_file(f) is False
```

```
git commit -m "test: red – VFSEntry, VFSRegistry, VFSProvider protocol, is_vfs_file"
```

---

### Step 3 – Green: `src/pykofinder/vfs.py`

Implement the module exactly as specified in §3.1 above (including the bottom
provider imports). Run:

```bash
timeout 120 uv run pytest tests/test_vfs.py -v
```

All tests must pass. Then run the full suite to check nothing broke:

```bash
timeout 120 uv run pytest --tb=short
```

```
git commit -m "feat: vfs.py – VFSEntry, VFSProvider, VFSRegistry, is_vfs_file"
```

---

### Step 4 – Red: `tests/test_providers_sqlite.py` (enumeration)

Create the file. All tests fail. Run to confirm.

Tests for schema/table enumeration:

```python
import sqlite3, pytest
from pathlib import Path
from pykofinder.providers.sqlite import SQLiteProvider, TABLE_ICON, SCHEMA_ICON, ROW_ICON

@pytest.fixture()
def single_schema_db(tmp_path):
    """SQLite DB with one schema (main) and two tables."""
    db = tmp_path / "test.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    con.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, amount REAL)")
    con.execute("INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob')")
    con.commit(); con.close()
    return db

@pytest.fixture()
def provider():
    return SQLiteProvider()

# test_handles_db_extension
#   provider.handles(Path("foo.db")) is True

# test_handles_DB_uppercase
#   provider.handles(Path("foo.DB")) is True

# test_does_not_handle_csv
#   provider.handles(Path("foo.csv")) is False

# test_does_not_handle_txt
#   provider.handles(Path("data.txt")) is False

# test_list_entries_empty_vpath_returns_tables_single_schema(single_schema_db, provider)
#   entries = provider.list_entries(single_schema_db, "")
#   names = [e.name for e in entries]
#   "users" in names and "orders" in names

# test_list_entries_tables_are_folders(single_schema_db, provider)
#   entries = provider.list_entries(single_schema_db, "")
#   all(e.is_folder for e in entries)

# test_list_entries_table_icon(single_schema_db, provider)
#   entries = provider.list_entries(single_schema_db, "")
#   all(e.icon == TABLE_ICON for e in entries)

# test_list_entries_table_vpath_is_table_name(single_schema_db, provider)
#   entries = provider.list_entries(single_schema_db, "")
#   vpaths = {e.vpath for e in entries}
#   "users" in vpaths and "orders" in vpaths

# test_list_entries_skips_sqlite_internal_tables(tmp_path, provider)
#   db = tmp_path / "x.db"
#   con = sqlite3.connect(str(db)); con.execute("CREATE VIRTUAL TABLE ...")
#   # Simpler: just assert no entry named "sqlite_sequence" etc.
#   con.execute("CREATE TABLE t (x)"); con.commit(); con.close()
#   entries = provider.list_entries(db, "")
#   assert all(not e.name.startswith("sqlite_") for e in entries)

# test_list_entries_returns_empty_list_on_bad_path(provider)
#   entries = provider.list_entries(Path("/nonexistent/fake.db"), "")
#   entries == []

# test_default_fmt_returns_folders(provider)
#   provider.default_fmt("") == "folders"
#   provider.default_fmt("users") == "folders"
```

```
git commit -m "test: red – SQLiteProvider handles() + table enumeration"
```

---

### Step 5 – Green: providers package + SQLiteProvider enumeration (schema/table)

Create `src/pykofinder/providers/__init__.py` (empty).

Create `src/pykofinder/providers/sqlite.py` with the complete structure from §3.3,
implementing only `handles`, `default_fmt`, `list_entries` (schema/table level, not
row level yet) and stub `render_preview` that returns a placeholder string.

Run:

```bash
timeout 120 uv run pytest tests/test_providers_sqlite.py tests/test_vfs.py -v
```

```
git commit -m "feat: providers package + SQLiteProvider handles() + table enumeration"
```

---

### Step 6 – Red: row enumeration + row-key derivation tests

Extend `tests/test_providers_sqlite.py`. All new tests fail.

```python
# test_list_entries_for_table_vpath_returns_row_entries(single_schema_db, provider)
#   entries = provider.list_entries(single_schema_db, "users")
#   assert len(entries) == 2  (Alice id=1, Bob id=2)

# test_row_entries_have_row_icon(single_schema_db, provider)
#   entries = provider.list_entries(single_schema_db, "users")
#   all(e.icon == ROW_ICON for e in entries)

# test_row_entries_are_not_folders(single_schema_db, provider)
#   entries = provider.list_entries(single_schema_db, "users")
#   all(not e.is_folder for e in entries)

# test_row_key_single_pk(single_schema_db, provider)
#   entries = provider.list_entries(single_schema_db, "users")
#   vpaths = {e.vpath for e in entries}
#   "users/1" in vpaths and "users/2" in vpaths

# test_row_key_no_pk_uses_rowid(tmp_path, provider)
#   db = tmp_path / "nopk.db"
#   con = sqlite3.connect(str(db))
#   con.execute("CREATE TABLE t (name TEXT)")
#   con.execute("INSERT INTO t VALUES ('x'), ('y')")
#   con.commit(); con.close()
#   entries = provider.list_entries(db, "t")
#   all(e.vpath.startswith("t/row_") for e in entries)

# test_row_key_unique_first_col(tmp_path, provider)
#   db = tmp_path / "uniq.db"
#   con = sqlite3.connect(str(db))
#   con.execute("CREATE TABLE t (code TEXT, val INTEGER)")
#   con.execute("INSERT INTO t VALUES ('A', 1), ('B', 2)")
#   con.commit(); con.close()
#   entries = provider.list_entries(db, "t")
#   vpaths = {e.vpath for e in entries}
#   "t/A" in vpaths and "t/B" in vpaths

# test_row_key_non_unique_first_col_falls_back_to_rowid(tmp_path, provider)
#   db with table t (name TEXT), two rows with same name "dup"
#   entries = provider.list_entries(db, "t")
#   all(e.vpath.startswith("t/row_") for e in entries)

# test_row_key_blob_value_shown_as_binary_note(tmp_path, provider)
#   db with table t (id INTEGER PRIMARY KEY, data BLOB)
#   insert row with data = b'\x00\x01\x02'
#   entries = provider.list_entries(db, "t")  → id=1 → "t/1" (PK wins)
#   (blob is in non-PK column so PK key is used; test passes if vpath == "t/1")

# test_row_key_truncates_long_pk(tmp_path, provider)
#   db with table t (id TEXT PRIMARY KEY)
#   insert row with id = "x" * 80
#   entry = provider.list_entries(db, "t")[0]
#   assert len(entry.name) == 60 and entry.name.endswith("…")

# test_list_entries_max_row_entries_cap(tmp_path, provider)
#   db with table t (id INTEGER PRIMARY KEY), 501 rows
#   entries = provider.list_entries(db, "t")
#   assert len(entries) == 501  (500 rows + 1 info sentinel)
#   assert entries[-1].name.startswith("(first 500")

# test_list_entries_row_vpath_format(single_schema_db, provider)
#   entries = provider.list_entries(single_schema_db, "users")
#   for e in entries: assert e.vpath.startswith("users/")
```

```
git commit -m "test: red – SQLiteProvider row enumeration + row-key derivation"
```

---

### Step 7 – Green: row enumeration + row-key derivation

Implement `_list_rows`, `_row_key` in `providers/sqlite.py` as specified in §3.3.
Extend `_list_entries_inner` to handle depth-1 (single-schema table name) and
depth-2 (multi-schema schema/table).

Run:

```bash
timeout 120 uv run pytest tests/test_providers_sqlite.py -v
```

```
git commit -m "feat: SQLiteProvider row enumeration + row-key derivation (PK→unique col→rowid)"
```

---

### Step 8 – Red: `render_preview` tests

Extend `tests/test_providers_sqlite.py`. All new tests fail.

```python
# test_render_preview_spreadsheet_has_db_table_class(single_schema_db, provider)
#   html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
#   assert "db-table" in html

# test_render_preview_spreadsheet_has_column_headers(single_schema_db, provider)
#   html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
#   assert "<th>id</th>" in html or "id" in html
#   assert "<th>name</th>" in html or "name" in html

# test_render_preview_spreadsheet_has_data(single_schema_db, provider)
#   html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
#   assert "Alice" in html and "Bob" in html

# test_render_preview_spreadsheet_has_fmt_bar(single_schema_db, provider)
#   html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
#   assert "fmt-bar" in html

# test_render_preview_spreadsheet_active_button_is_spreadsheet(single_schema_db, provider)
#   html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
#   assert "📊 Spreadsheet" in html
#   # Active button is the spreadsheet one
#   assert 'class="fmt-btn active"' in html or "fmt-btn active" in html

# test_render_preview_spreadsheet_rows_button_has_correct_col(single_schema_db, provider)
#   html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, col=3)
#   assert "#col-3" in html  (the hx-target for the Rows toggle)

# test_render_preview_spreadsheet_single_page_no_pagination_links(single_schema_db, provider)
#   html = provider.render_preview(single_schema_db, "users", "spreadsheet", 1, 1000, 0)
#   # only 2 rows, limit 1000 → single page → no Prev/Next links
#   assert "← Prev" not in html
#   assert "Next →" not in html

# test_render_preview_spreadsheet_page1_has_next_link(tmp_path, provider)
#   db with 5 rows; render with limit=2, page=1
#   html = provider.render_preview(db, "t", "spreadsheet", 1, 2, 0)
#   assert "Next →" in html
#   assert "← Prev" not in html

# test_render_preview_spreadsheet_page2_has_both_links(tmp_path, provider)
#   db with 5 rows; render with limit=2, page=2
#   html = provider.render_preview(db, "t", "spreadsheet", 2, 2, 0)
#   assert "← Prev" in html and "Next →" in html

# test_render_preview_spreadsheet_last_page_has_no_next(tmp_path, provider)
#   db with 4 rows; render with limit=2, page=2
#   html = provider.render_preview(db, "t", "spreadsheet", 2, 2, 0)
#   assert "← Prev" in html
#   assert "Next →" not in html

# test_render_preview_spreadsheet_empty_table(tmp_path, provider)
#   db with empty table t; render
#   html = provider.render_preview(db, "t", "spreadsheet", 1, 1000, 0)
#   assert "empty" in html.lower()

# test_render_preview_kv_has_kv_table_class(single_schema_db, provider)
#   html = provider.render_preview(single_schema_db, "users/1", "folders", 1, 1000, 0)
#   assert "db-kv-table" in html

# test_render_preview_kv_shows_field_values(single_schema_db, provider)
#   html = provider.render_preview(single_schema_db, "users/1", "folders", 1, 1000, 0)
#   assert "Alice" in html

# test_render_preview_kv_no_fmt_bar(single_schema_db, provider)
#   html = provider.render_preview(single_schema_db, "users/1", "folders", 1, 1000, 0)
#   assert "fmt-bar" not in html

# test_render_preview_blob_shows_binary_note(tmp_path, provider)
#   db with table t (id INTEGER PRIMARY KEY, data BLOB)
#   insert (1, b'\x00\x01\x02')
#   html = provider.render_preview(db, "t/1", "folders", 1, 1000, 0)
#   assert "binary data" in html and "3 bytes" in html

# test_render_preview_long_string_truncated_in_spreadsheet(tmp_path, provider)
#   db with table t (id INTEGER PRIMARY KEY, note TEXT)
#   insert (1, "x" * 300)
#   html = provider.render_preview(db, "t", "spreadsheet", 1, 1000, 0)
#   assert "…" in html  (truncated in cell)

# test_render_preview_long_string_full_in_kv(tmp_path, provider)
#   same db; render KV for row 1
#   html = provider.render_preview(db, "t/1", "folders", 1, 1000, 0)
#   assert "x" * 300 in html  (no truncation in KV detail)

# test_render_preview_pagination_links_have_vpage_href(tmp_path, provider)
#   db with 3 rows; render limit=1, page=1
#   html = provider.render_preview(db, "t", "spreadsheet", 1, 1, 0)
#   assert "/vpage" in html

# test_render_preview_unknown_vpath_returns_error_or_message(provider, tmp_path)
#   db = tmp_path / "x.db"; sqlite3.connect(str(db)).close()
#   html = provider.render_preview(db, "nonexistent_table", "spreadsheet", 1, 1000, 0)
#   # Should not crash; returns either error div or empty-table message
#   assert "preview-error" in html or "empty" in html.lower() or "db-table" in html
```

```
git commit -m "test: red – SQLiteProvider render_preview (spreadsheet + KV row detail)"
```

---

### Step 9 – Green: `render_preview` implementation

Implement `render_preview`, `_render_inner`, `_render_spreadsheet`, `_render_kv`,
`_cell_val` in `providers/sqlite.py` as specified in §3.3.

Run:

```bash
timeout 120 uv run pytest tests/test_providers_sqlite.py -v
```

Then full suite:

```bash
timeout 120 uv run pytest --tb=short
```

```
git commit -m "feat: SQLiteProvider render_preview – spreadsheet with pagination + KV row detail"
```

---

### Step 10 – Red: stub provider tests

Add to `tests/test_vfs.py` (or new `tests/test_providers_stubs.py`):

```python
# test_csv_provider_registered(tmp_path)
#   from pykofinder.vfs import REGISTRY
#   f = tmp_path / "data.csv"; f.touch()
#   provider = REGISTRY.get(f)
#   assert provider is not None

# test_csv_provider_default_fmt_is_spreadsheet(tmp_path)
#   f = tmp_path / "data.csv"; f.touch()
#   provider = REGISTRY.get(f)
#   assert provider.default_fmt("") == "spreadsheet"

# test_json_provider_registered(tmp_path)
#   from pykofinder.vfs import REGISTRY
#   f = tmp_path / "data.json"; f.touch()
#   provider = REGISTRY.get(f)
#   assert provider is not None

# test_json_provider_default_fmt_is_formatted(tmp_path)
#   f = tmp_path / "data.json"; f.touch()
#   provider = REGISTRY.get(f)
#   assert provider.default_fmt("") == "formatted"
```

```
git commit -m "test: red – CSV + JSON stub provider registration"
```

---

### Step 11 – Green: stub providers

Create `src/pykofinder/providers/csv_provider.py` and
`src/pykofinder/providers/json_provider.py` exactly as in §3.4 and §3.5.

Run:

```bash
timeout 120 uv run pytest tests/test_vfs.py -v
timeout 120 uv run pytest --tb=short
```

```
git commit -m "feat: CSV + JSON stub providers (registered; default fmts: spreadsheet, formatted)"
```

---

### Step 12 – Red: `entry_icon` and `list_column` changes in columns

Extend `tests/test_columns.py`:

```python
# test_entry_icon_db(tmp_path)
#   f = tmp_path / "data.db"; f.touch()
#   assert entry_icon(f) == "🗄️"

# test_list_column_db_file_targets_next_col(tmp_path)
#   db = tmp_path / "data.db"; db.touch()
#   html = list_column(tmp_path, tmp_path, col_index=1).__html__()
#   assert "col-2" in html  (hx-target for the db file)

# test_list_column_db_file_does_not_target_preview(tmp_path)
#   db = tmp_path / "data.db"; db.touch()
#   html = list_column(tmp_path, tmp_path, col_index=1).__html__()
#   # The db file link should NOT target #preview
#   # (md file still targets preview, db file targets next col)
#   md = tmp_path / "note.md"; md.touch()
#   html = list_column(tmp_path, tmp_path, col_index=1).__html__()
#   # Verify md still targets preview (regression check)
#   assert "#preview" in html
```

For `list_vfs_column`:

```python
# test_list_vfs_column_renders_folder_entries(tmp_path)
#   from pykofinder.vfs import VFSEntry
#   from pykofinder.columns import list_vfs_column
#   entries = [VFSEntry(name="users", vpath="users", is_folder=True, icon="🗃️")]
#   html = list_vfs_column(entries, "foo.db", "/abs/foo.db", "", 1).__html__()
#   assert "users" in html

# test_list_vfs_column_folder_targets_next_col(tmp_path)
#   entries = [VFSEntry(name="users", vpath="users", is_folder=True, icon="🗃️")]
#   html = list_vfs_column(entries, "foo.db", "/abs/foo.db", "", col_index=2).__html__()
#   assert "col-3" in html

# test_list_vfs_column_leaf_targets_preview(tmp_path)
#   entries = [VFSEntry(name="row_1", vpath="users/1", is_folder=False, icon="📋")]
#   html = list_vfs_column(entries, "foo.db", "/abs/foo.db", "users", col_index=2).__html__()
#   assert "preview" in html

# test_list_vfs_column_fmt_bar_absent_when_not_requested(tmp_path)
#   entries = [VFSEntry(name="users", vpath="users", is_folder=True, icon="🗃️")]
#   html = list_vfs_column(entries, "foo.db", "/abs/foo.db", "", col_index=1,
#                           show_fmt_bar=False).__html__()
#   assert "fmt-bar" not in html

# test_list_vfs_column_fmt_bar_present_when_requested(tmp_path)
#   entries = [VFSEntry(name="r1", vpath="users/1", is_folder=False, icon="📋")]
#   html = list_vfs_column(entries, "foo.db", "/abs/foo.db", "users", col_index=2,
#                           show_fmt_bar=True).__html__()
#   assert "fmt-bar" in html

# test_list_vfs_column_fmt_bar_active_is_rows(tmp_path)
#   html = list_vfs_column([...], ..., show_fmt_bar=True, active_fmt="folders").__html__()
#   # The Rows button should have "active" class
#   assert "📋 Rows" in html
#   # Spreadsheet button should NOT have "active"
#   assert "📊 Spreadsheet" in html

# test_list_vfs_column_url_has_vpath(tmp_path)
#   entries = [VFSEntry(name="users", vpath="users", is_folder=True, icon="🗃️")]
#   html = list_vfs_column(entries, "foo.db", "/abs/foo.db", "", col_index=1).__html__()
#   assert "vpath=users" in html

# test_list_vfs_column_col_id(tmp_path)
#   html = list_vfs_column([], "f.db", "/f.db", "", col_index=5).__html__()
#   assert 'id="col-5"' in html

# test_list_vfs_column_prune_script_present(tmp_path)
#   html = list_vfs_column([], "f.db", "/f.db", "", col_index=3).__html__()
#   assert "<script>" in html

# test_list_vfs_column_data_fpath_on_entries(tmp_path)
#   entries = [VFSEntry(name="users", vpath="users", is_folder=True, icon="🗃️")]
#   html = list_vfs_column(entries, "f.db", "/abs/f.db", "", col_index=1).__html__()
#   assert "data-fpath" in html

# test_render_breadcrumb_with_vpath(tmp_path)
#   from pykofinder.columns import render_breadcrumb
#   html = render_breadcrumb(tmp_path / "foo.db", tmp_path, vpath="users")
#   assert "users" in html
#   assert "bc-virtual" in html

# test_render_breadcrumb_with_nested_vpath(tmp_path)
#   html = render_breadcrumb(tmp_path / "foo.db", tmp_path, vpath="users/42")
#   assert "users" in html and "42" in html
```

```
git commit -m "test: red – entry_icon .db, list_column VFS routing, list_vfs_column, breadcrumb vpath"
```

---

### Step 13 – Green: columns.py changes

1. Add `import html as html_lib` to `columns.py` if not already present.
2. Add `from pykofinder.vfs import is_vfs_file` import.
3. Update `entry_icon()` with `.db → 🗄️`.
4. Update `render_breadcrumb()` with `vpath=""` parameter and virtual segments.
5. Update `list_column()` with the `elif is_vfs_file(p):` branch.
6. Implement `list_vfs_column()` as specified in §3.6.

Run:

```bash
timeout 120 uv run pytest tests/test_columns.py -v
timeout 120 uv run pytest --tb=short
```

```
git commit -m "feat: columns.py – 🗄️ icon, VFS file routing, list_vfs_column(), breadcrumb vpath"
```

---

### Step 14 – Red: CSS presence tests

Extend `tests/test_app.py` (or add to `tests/test_rendering.py`):

```python
from pykofinder.styles import APP_CSS

# test_app_css_has_fmt_bar
#   assert ".fmt-bar" in APP_CSS

# test_app_css_has_fmt_btn
#   assert ".fmt-btn" in APP_CSS

# test_app_css_has_fmt_btn_active
#   assert ".fmt-btn.active" in APP_CSS

# test_app_css_has_preview_db_spreadsheet
#   assert "preview-db-spreadsheet" in APP_CSS

# test_app_css_has_db_table
#   assert "db-table" in APP_CSS

# test_app_css_has_db_table_wrap
#   assert "db-table-wrap" in APP_CSS

# test_app_css_has_db_kv_table
#   assert "db-kv-table" in APP_CSS

# test_app_css_has_db_pagination
#   assert "db-pagination" in APP_CSS

# test_app_css_has_bc_virtual
#   assert "bc-virtual" in APP_CSS
```

```
git commit -m "test: red – CSS class presence for VFS/DB styles"
```

---

### Step 15 – Green: CSS additions

Append the full CSS block from §3.8 to `APP_CSS` in `styles.py`.

> **Risk mitigation (`.column { display:flex }`):** After adding the CSS, run all
> existing `test_list_column_*` and `test_initial_columns_*` tests. If any fail,
> scope the flex rule: rename `.column { display:flex; flex-direction:column }` to
> `.column.vfs-column { … }` and add `cls="column vfs-column"` in `list_vfs_column`.
> Do NOT scope it if existing tests still pass.

Run:

```bash
timeout 120 uv run pytest tests/ -v --tb=short
```

```
git commit -m "style: APP_CSS – fmt-bar, db-table, db-kv, db-pagination, bc-virtual"
```

---

### Step 16 – Red: JS presence tests

Extend `tests/test_app.py`:

```python
from pykofinder.styles import COLUMN_JS

# test_column_js_has_htmx_config_request_listener
#   assert "htmx:configRequest" in COLUMN_JS

# test_column_js_has_vfmt_file_key
#   assert "vfmt_file_" in COLUMN_JS

# test_column_js_has_vfmt_type_key
#   assert "vfmt_type_" in COLUMN_JS

# test_column_js_has_local_storage_set_item
#   assert "localStorage.setItem" in COLUMN_JS

# test_column_js_has_fmt_btn_click_handler
#   assert ".fmt-btn[data-fmt]" in COLUMN_JS or "fmt-btn" in COLUMN_JS
```

```
git commit -m "test: red – format-persistence JS presence assertions"
```

---

### Step 17 – Green: JS additions

Append the JS block from §3.8 to `COLUMN_JS` in `styles.py`.

Run:

```bash
timeout 120 uv run pytest tests/ -v --tb=short
```

```
git commit -m "feat: COLUMN_JS – VFS format persistence (htmx:configRequest + localStorage toggle)"
```

---

### Step 18 – Red: `/click` VFS dispatch + `/vpage` tests

Add a `db_fixture` fixture to `tests/conftest.py`:

```python
import sqlite3

@pytest.fixture()
def db_root(tmp_path: Path):
    """tmp_root with a SQLite .db file containing a users table (5 rows)."""
    (tmp_path / "subdir").mkdir()
    db = tmp_path / "sample.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, bio TEXT)")
    for i in range(1, 6):
        con.execute("INSERT INTO users VALUES (?, ?, ?)", (i, f"User{i}", f"Bio{i}"))
    con.commit(); con.close()
    original = app_module.ROOT
    app_module.ROOT = tmp_path
    yield tmp_path
    app_module.ROOT = original


@pytest.fixture()
def db_client(db_root: Path):
    return TestClient(app_module.app, raise_server_exceptions=False)
```

Add tests in `tests/test_app.py`:

```python
from urllib.parse import quote

# test_click_db_file_returns_vfs_column(db_client, db_root)
#   db = db_root / "sample.db"
#   resp = db_client.get(f"/click?path={quote(str(db))}&col=1")
#   assert resp.status_code == 200
#   assert "col-1" in resp.text
#   assert "users" in resp.text   (table name in the column)
#   assert "preview" not in resp.text.lower()[:500]  (no preview content)

# test_click_db_vpath_table_fmt_folders_returns_row_column(db_client, db_root)
#   db = db_root / "sample.db"
#   resp = db_client.get(f"/click?path={quote(str(db))}&col=2&vpath=users&fmt=folders")
#   assert resp.status_code == 200
#   assert "col-2" in resp.text   (new column id)
#   assert "📋" in resp.text or "ROW" in resp.text  (row entries)

# test_click_db_vpath_table_fmt_spreadsheet_returns_sentinel_plus_oob_preview(db_client, db_root)
#   db = db_root / "sample.db"
#   resp = db_client.get(f"/click?path={quote(str(db))}&col=2&vpath=users&fmt=spreadsheet")
#   assert resp.status_code == 200
#   assert "db-table" in resp.text   (spreadsheet in OOB preview)
#   assert 'id="col-2"' in resp.text  (sentinel present)
#   assert "hx-swap-oob" in resp.text  (OOB swap marker)

# test_click_db_vpath_row_returns_kv_preview(db_client, db_root)
#   db = db_root / "sample.db"
#   resp = db_client.get(f"/click?path={quote(str(db))}&col=3&vpath=users%2F1")
#   assert resp.status_code == 200
#   assert "db-kv-table" in resp.text
#   assert "User1" in resp.text

# test_click_db_breadcrumb_oob_present(db_client, db_root)
#   db = db_root / "sample.db"
#   resp = db_client.get(f"/click?path={quote(str(db))}&col=2&vpath=users&fmt=folders")
#   assert "breadcrumb" in resp.text
#   assert "hx-swap-oob" in resp.text

# test_click_db_bad_path_returns_access_denied(db_client, db_root)
#   resp = db_client.get("/click?path=/etc/passwd&col=1")
#   assert "Access denied" in resp.text

# test_vpage_returns_spreadsheet_html(db_client, db_root)
#   db = db_root / "sample.db"
#   resp = db_client.get(f"/vpage?path={quote(str(db))}&vpath=users&page=1&limit=1000")
#   assert resp.status_code == 200
#   assert "db-table" in resp.text
#   assert "User1" in resp.text

# test_vpage_page2_offset_correct(db_client, db_root)
#   db = db_root / "sample.db"
#   resp1 = db_client.get(f"/vpage?path={quote(str(db))}&vpath=users&page=1&limit=2")
#   resp2 = db_client.get(f"/vpage?path={quote(str(db))}&vpath=users&page=2&limit=2")
#   # Page 1 has User1, User2; Page 2 has User3, User4
#   assert "User1" in resp1.text and "User3" not in resp1.text
#   assert "User3" in resp2.text and "User1" not in resp2.text

# test_vpage_bad_path_returns_404(db_client)
#   resp = db_client.get("/vpage?path=/nonexistent.db&vpath=t&page=1&limit=10")
#   assert resp.status_code == 404

# test_vpage_no_provider_for_extension_returns_404(db_client, db_root)
#   md = db_root / "readme.md"
#   md.touch()  # .md has no VFS provider
#   resp = db_client.get(f"/vpage?path={quote(str(md))}&vpath=&page=1&limit=10")
#   assert resp.status_code == 404
```

```
git commit -m "test: red – /click VFS dispatch + /vpage endpoint"
```

---

### Step 19 – Green: extend `/click` + add `/vpage` in `app.py`

1. Add imports: `from pykofinder.vfs import REGISTRY`, `from pykofinder.columns import
list_vfs_column`, `from textwrap import dedent`.
2. Implement `_make_bc_oob(path, vpath="")` and `_build_prune_js(col)` helpers.
3. Replace the `click()` function body with the VFS dispatch logic from §3.7.
4. Add the `/vpage` endpoint from §3.7.

Keep the existing real-dir and file-preview branches **unchanged in behaviour**
(use the helpers for DRY but don't alter the logic).

Run:

```bash
timeout 120 uv run pytest tests/test_app.py -v --tb=short
timeout 120 uv run pytest --tb=short
```

```
git commit -m "feat: /click VFS dispatch (vpath+fmt) + /vpage pagination endpoint"
```

---

### Step 20 – Integration smoke test

Create `tests/test_integration_vfs.py`:

```python
import sqlite3
import pytest
from pathlib import Path
from urllib.parse import quote
from starlette.testclient import TestClient
import pykofinder.app as app_module


@pytest.fixture()
def int_root(tmp_path):
    db = tmp_path / "movies.db"
    con = sqlite3.connect(str(db))
    con.execute(
        "CREATE TABLE films (id INTEGER PRIMARY KEY, title TEXT, year INTEGER)"
    )
    for i in range(1, 12):   # 11 rows → pagination test with limit=5
        con.execute("INSERT INTO films VALUES (?, ?, ?)", (i, f"Film {i}", 2000 + i))
    con.commit(); con.close()
    original = app_module.ROOT
    app_module.ROOT = tmp_path
    yield tmp_path
    app_module.ROOT = original


@pytest.fixture()
def int_client(int_root):
    return TestClient(app_module.app, raise_server_exceptions=False)


# test_db_navigation_level0_shows_tables_column(int_client, int_root)
#   db = int_root / "movies.db"
#   resp = int_client.get(f"/click?path={quote(str(db))}&col=1")
#   assert "films" in resp.text
#   assert 'id="col-1"' in resp.text

# test_db_navigation_level1_folders_shows_row_column(int_client, int_root)
#   db = int_root / "movies.db"
#   resp = int_client.get(f"/click?path={quote(str(db))}&col=2&vpath=films&fmt=folders")
#   assert "📋" in resp.text or "row_" in resp.text or "Film" in resp.text
#   assert 'id="col-2"' in resp.text

# test_db_navigation_level1_spreadsheet_shows_preview(int_client, int_root)
#   db = int_root / "movies.db"
#   resp = int_client.get(f"/click?path={quote(str(db))}&col=2&vpath=films&fmt=spreadsheet")
#   assert "db-table" in resp.text
#   assert "Film 1" in resp.text

# test_db_navigation_level2_row_detail(int_client, int_root)
#   db = int_root / "movies.db"
#   resp = int_client.get(f"/click?path={quote(str(db))}&col=3&vpath=films%2F1")
#   assert "db-kv-table" in resp.text
#   assert "Film 1" in resp.text

# test_vpage_pagination_limit(int_client, int_root)
#   db = int_root / "movies.db"
#   r1 = int_client.get(f"/vpage?path={quote(str(db))}&vpath=films&page=1&limit=5")
#   r3 = int_client.get(f"/vpage?path={quote(str(db))}&vpath=films&page=3&limit=5")
#   assert "Film 1" in r1.text and "Film 6" not in r1.text
#   assert "Film 11" in r3.text

# test_breadcrumb_shows_vpath_segments(int_client, int_root)
#   db = int_root / "movies.db"
#   resp = int_client.get(f"/click?path={quote(str(db))}&col=2&vpath=films&fmt=folders")
#   assert "films" in resp.text   (vpath in breadcrumb)

# test_existing_dir_navigation_still_works(int_client, int_root)
#   sub = int_root / "docs"; sub.mkdir()
#   resp = int_client.get(f"/click?path={quote(str(int_root))}&col=1")
#   assert "docs" in resp.text

# test_existing_file_preview_still_works(int_client, int_root)
#   md = int_root / "readme.md"; md.write_text("# Hello")
#   resp = int_client.get(f"/click?path={quote(str(md))}&col=1")
#   assert "Hello" in resp.text
```

```
git commit -m "test: integration smoke – DB VFS navigation + existing FS navigation regression"
```

---

### Step 21 – Full suite green + coverage

```bash
timeout 120 uv run pytest --tb=short -q
```

All tests must pass. If there are failures, fix them before proceeding.

Check coverage:

```bash
timeout 120 uv run pytest --cov-report=term-missing --tb=short -q
```

Add `# pragma: no cover` only for genuinely unreachable branches (e.g., the
`except` in `_preview_pdf` that requires a truly exceptional OS failure); add an
inline comment explaining why.

```
git commit -m "test: confirm 100% branch coverage; add pragma: no cover where warranted"
```

---

### Step 22 – Close issue #18

In `ISSUES.md`:

- Change `**Status:** in-progress` → `**Status:** closed`
- Add `**Closed:** <today's date>`
- Add `**Prune after:** <today + 90 days>`
- Add an `**Implemented:**` block:

```markdown
**Implemented:**

- `src/pykofinder/vfs.py` – `VFSEntry`, `VFSProvider` (Protocol), `VFSRegistry`,
  `REGISTRY` singleton, `is_vfs_file()`, `_truncate()`
- `src/pykofinder/providers/__init__.py` – package marker
- `src/pykofinder/providers/sqlite.py` – `SQLiteProvider` with schema/table/row
  enumeration, row-key derivation (PK → unique col → rowid), spreadsheet preview
  (paginated), KV row-detail preview, BLOB handling
- `src/pykofinder/providers/csv_provider.py` – stub (`default_fmt="spreadsheet"`)
- `src/pykofinder/providers/json_provider.py` – stub (`default_fmt="formatted"`)
- `src/pykofinder/columns.py` – `list_vfs_column()`, `🗄️` icon for `.db`,
  VFS-file routing in `list_column()`, `vpath` param in `render_breadcrumb()`
- `src/pykofinder/app.py` – `/click` VFS dispatch (`vpath`, `fmt` params),
  `_make_bc_oob()`, `_build_prune_js()` helpers, `/vpage` endpoint
- `src/pykofinder/styles.py` – VFS/DB CSS, format-persistence JS (localStorage)
- `tests/test_vfs.py`, `tests/test_providers_sqlite.py`,
  `tests/test_integration_vfs.py` – new test files
```

In `TASKS.md`:

- Move `[~] #18 …` from **In progress** to **Done** with the prune-after date in a
  comment (same format as other done items).

```
git commit -m "docs: close issue #18 in ISSUES.md and TASKS.md"
```

---

## 5 · Known risks and mitigations

| Risk                                             | Mitigation                                                                                                                                                                                                      |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Circular import (`vfs.py` ↔ providers)          | All `vfs.py` names are bound before the bottom-of-file imports; Python's module cache prevents double execution. If it causes `ImportError`, move to a lazy `_register_providers()` guard.                      |
| `.column { display:flex }` CSS layout regression | Run full test suite after Step 15. If visual tests or layout tests fail, scope to `.column.vfs-column`.                                                                                                         |
| `has_format_toggle` complexity                   | Removed from protocol; `show_fmt_bar` determined in `/click` by checking `any(e.icon == "📋" for e in entries)`.                                                                                                |
| Row-key uniqueness scan is a full-table scan     | Capped at `MAX_ROW_ENTRIES` rows in both the count queries; acceptable at 500 rows.                                                                                                                             |
| `htmx:configRequest` fires for all HTMX links    | Guard: `if (fpath === undefined) return;` – only VFS links have `data-fpath`.                                                                                                                                   |
| `vpath` URL encoding                             | Use `urlquote(entry.vpath)` in `list_vfs_column`; server receives decoded string via Starlette's query-param binding.                                                                                           |
| Multi-schema SQLite edge case                    | Use `PRAGMA database_list` to distinguish schemas from tables; the depth-based dispatch in `_list_entries_inner` handles both single and multi-schema.                                                          |
| `/click` backward compatibility                  | `vpath=""` and `fmt=""` defaults; REGISTRY.get() returns None for all existing real-FS files (non-.db/csv/json); VFS block is skipped entirely. Existing tests hit only the real-dir and file-preview branches. |
| KV row lookup by non-rowid key                   | Fallback: iterate up to MAX_ROW_ENTRIES rows and match by reconstructed key. For large tables this is inefficient; acceptable for v1.                                                                           |
| FastHTML `Div(id=…)` sentinel serialisation      | FastHTML renders `Div(id="col-2")` as `<div id="col-2"></div>`. This is the empty sentinel. Verify by calling `.__html__()` in tests.                                                                           |

---

## 6 · Acceptance criteria

- [ ] Clicking a `.db` file in the column view opens a **tables column** (not a preview).
- [ ] Clicking a table in the tables column shows **rows as folder entries** (default `folders` mode).
- [ ] The rows column has a **"📊 Spreadsheet"** toggle button that switches to spreadsheet view.
- [ ] The spreadsheet preview has a **"📋 Rows"** toggle button that switches back to folder view.
- [ ] Switching format **persists in localStorage** per file path and per type.
- [ ] Clicking a row entry shows a **key-value table** in the preview pane (no column opened).
- [ ] Spreadsheet view supports **server-side pagination** via `/vpage` (1 000 rows/page default).
- [ ] `← Prev` / `Next →` links work correctly on page boundaries.
- [ ] **BLOB fields** display as `⟨binary data, N bytes⟩`.
- [ ] **Long strings** (> 200 chars) are truncated in spreadsheet cells; full value shown in KV detail.
- [ ] **Row keys** are derived: PK → composite PK → unique first col → `row_N`.
- [ ] SQLite files with **multiple schemas** show a schema folder level first.
- [ ] SQLite files with **only `main`** schema skip the schema level.
- [ ] **CSV** and **JSON** files are registered in the VFS registry (stubs; no navigation yet).
- [ ] **Breadcrumb** shows virtual path segments (in italic) when navigating inside a file.
- [ ] Existing real-filesystem navigation and all existing tests still pass with 100% coverage.
