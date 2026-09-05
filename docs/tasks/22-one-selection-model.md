---
depends-on: [18]
---

# One selection model

## Goal

The selection has one source of truth. `sel[i]` is the selected name in
column `i`. The row index is computed when needed. Roadmap phase 4, step 2.

## Steps

1. List every use of `cursor[i]`, `sel[i]` and `node.lastSel` in `ui/core/`:
   `grep -n "cursor\[\|lastSel" ui/core/*.js`.
2. Add `rowIndex(node, name)` in `ui/core/state.js`. It returns the index of
   `name` in `node.kids`, or `-1`.
3. Replace each read of `cursor[i]` with `rowIndex(node, sel[i])`.
4. Replace each write of `cursor[i]` with a write of `sel[i]`.
5. Replace `node.lastSel` with `sel[i]` for that column. If back-navigation
   needs the last selection, keep one map `lastSel[path] = name` in `state.js`.
6. Delete `cursor`.

## Done when

- `grep -n "cursor\[\|lastSel" ui/core/*.js` prints nothing, except the one
  map in `state.js` if step 5 needs it.
- All keyboard tests in `static/test-ui.py` and
  `server/tests/test_browser_keyboard.py` pass.

## Scope

`ui/core/{state.js,nav.js,render.js}`.
