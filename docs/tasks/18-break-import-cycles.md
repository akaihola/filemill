---
depends-on: [17]
---

# Break the import cycles in ui/core/

## Goal

No file in `ui/core/` imports a file that imports it back. Roadmap phase 3,
step 4.

## Steps

1. Find the cycles. For each file, list its imports. Draw the graph on paper.
   `render.js` and `nav.js` import each other. `layout.js` imports DOM
   helpers from a file that imports `layout.js`.
2. Change `render.js` so it does not import `choose`, `unfoldTo` or
   `refreshColumn`. Add `export function setActions(actions)` that stores an
   object `{choose, unfoldTo, refreshColumn}`. The entry module calls it one
   time at boot.
3. Create `ui/core/dom.js` with `set(el, attrs)` and `setVar(name, value)`.
   Move those functions from their current file. `layout.js` imports them
   from `dom.js`.
4. Repeat until no cycle remains.

## Done when

- A script that walks the imports from `ui/entry-static.js` finds no cycle.
  A 20-line Python script with a `set` of visited files is enough.
- All static tests and server tests pass.

## Scope

`ui/core/render.js`, `ui/core/layout.js`, `ui/core/dom.js`, the entry modules.
