---
depends-on: []
---

# Delete the HTMX finder

## Goal

The server has one finder: the shared UI in `ui/`. No HTMX code, CSS,
JavaScript or test stays in the tree. Roadmap phase 0, step 1.

## Steps

1. In `server/src/filemill/app.py`, delete these functions: `click`, `vpage`,
   `restore`, `_finder_fragment`, `finder_root`, `finder_view`,
   `_build_prune_js`, `_make_bc_oob`, `_shell_html` and `_finder_url`.
2. Delete `server/src/filemill/columns.py`. Fix every import of it.
3. In `server/src/filemill/styles.py`, delete `COLUMN_JS`. In `APP_CSS`,
   delete each CSS rule that only the HTMX page used. A rule is HTMX-only when
   no file in `ui/` and no remaining Python file uses its selector.
4. In `server/src/filemill/providers/sqlite.py`, delete the HTMX pagination
   fragments (lines 378 to 419 on 2026-09-05).
5. In `server/tests/`, delete each test that fails because the code above is
   gone. Also delete the tests that check for substrings of `COLUMN_JS` or
   `APP_CSS`.
6. Run `cd server && uv run pytest`. Repeat steps 2 to 5 until it is green.

## Done when

- `grep -ri htmx server/src --exclude-dir=ui` prints nothing.
- `cd server && uv run pytest` passes.
- `git grep -n "columns.py\|COLUMN_JS"` prints nothing.

## Scope

`server/src/filemill/{app.py,columns.py,styles.py,providers/sqlite.py}` and
`server/tests/`. Do not change `ui/`.
