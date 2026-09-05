---
depends-on: [19]
---

# Make the SQLite provider return JSON only

## Goal

The server reads SQLite because the browser cannot. The server does not
render it. Tables and rows reach the client as JSON and the client shows
them with the same hierarchical view it uses for JSON files. Roadmap phase
6, step 3. This closes proposal [9]: the six-argument interface is gone.

## Steps

1. Read `providers/sqlite.py`. `list_entries` already feeds `/api/dir` with
   tables, rows and cells as entries. `render_preview`, `_render_spreadsheet`
   and `_render_kv` build HTML for `/api/preview`.
2. Add one JSON response for a row: `/api/dir?p=x.db&v=table/rowkey` already
   lists the cells. Make each cell entry carry `value` and `type` fields.
3. Add pagination as entries: when a table has more than 1 000 rows, the last
   entry of a page is `{name: "next", kind: "page", vpath: ...}`. The client
   opens it like a folder.
4. In `ui/adapters/vfs-json.js`, make the JSON hierarchical view accept these
   entries, so a table shows as a folder of rows and a row as a folder of
   key/value pairs, with the pretty-printed preview from task [5].
5. Delete `render_preview`, `_render_inner`, `_render_spreadsheet`,
   `_render_kv`, `default_fmt` and `_cell_val` in `sqlite.py`. Delete
   `render_preview` and `default_fmt` from the `VFSProvider` protocol in
   `vfs.py`. Delete `vfs_preview` in `api.py`.
6. Update `server/tests/test_providers_sqlite.py` and `test_api.py`: assert
   on JSON, not on HTML.
7. Move proposal [9] to `## Completed` in `TASKS.md`.

## Done when

- `grep -n "render_preview\|fmt" server/src/filemill/providers/sqlite.py` prints
  nothing.
- A `.db` file opens as columns in the server edition, and a row shows a
  key/value preview.
- All server tests and static tests pass.

## Scope

`providers/sqlite.py`, `vfs.py`, `api.py`, `ui/adapters/vfs-json.js`, tests.
