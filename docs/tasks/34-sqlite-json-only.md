---
depends-on: []
---

# Make the SQLite provider return JSON only

## Goal

The server reads SQLite because the browser cannot. The server does not
render it. Tables and rows reach the client as JSON and the client shows
them with the same hierarchical view it uses for JSON files. Roadmap phase
6, step 3. This closes proposal [9]: the six-argument interface is gone.

## Steps

1. Read `providers/sqlite.py`. `list_entries` already feeds `/api/dir` with
   tables and rows as entries. `render_preview`, `_render_spreadsheet` and
   `_render_kv` build HTML for `/api/preview`. The shared UI never previews
   a directory node, so the spreadsheet is reachable only by a direct API
   call.
2. Give `VFSEntry` an optional `record`. In `_list_rows`, fill it with the
   row's cells as JSON: `NULL` is `null`, a blob is a "binary data" note,
   everything else travels as it is. `/api/dir` emits `record` when set.
3. In `ui/adapters/http.js`, copy `record` onto the node. In
   `ui/adapters/vfs-json.js`, turn a listed row that carries a `record` into
   a JSON value node, so it browses like a JSONL record: the row opens as a
   column of cells and previews as pretty-printed JSON. The CSV wrapper in
   `vfs-csv.js` must draw only its own rows: it escapes values as strings,
   and a SQLite `id` is a number.
4. Delete `render_preview`, `_render_inner`, `_render_spreadsheet`,
   `_render_kv`, `default_fmt` and `_cell_val` in `sqlite.py`, and the
   `db-*` CSS in `styles.py`. Drop `render_preview` and `default_fmt` from
   the `VFSProvider` protocol; `vfs_preview` in `api.py` answers 404 for a
   provider without a renderer. VTT and JSON keep theirs until their own
   issue deletes them.
5. Update `server/tests/test_providers_sqlite.py` and `test_api.py`: assert
   on `record`, not on HTML.
6. Move proposal [9] to `## Completed` in `TASKS.md`.

## Done when

- `grep -n "render_preview\|fmt\|html" server/src/filemill/providers/sqlite.py`
  prints nothing.
- A `.db` file opens as columns in the server edition, and a row previews
  as JSON drawn by the client.
- All server tests and static tests pass.

## Scope

`providers/sqlite.py`, `vfs.py`, `api.py`, `styles.py`, `ui/adapters/http.js`,
`ui/adapters/vfs-json.js`, tests.

[9]: 9-vfs-viewspec.md
