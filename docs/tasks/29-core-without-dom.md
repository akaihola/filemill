---
depends-on: [18, 21]
---

# Make ui/core/ a model package with no DOM

## Goal

The model (nodes, selection, folding arithmetic, keyboard map, deep links)
runs without a browser. A thin renderer holds all DOM code. Roadmap phase 9,
step 1.

## Steps

1. Create `ui/core/model/`. Move the pure functions there: `sortKids`,
   the fold arithmetic from `layout.js`, the key map from `nav.js`, and the
   deep-link parse and format functions from `deeplink.js`.
2. Rule for the split: a file in `model/` must not use `document`, `window`
   or `Element`. Check with `grep -n "document\|window\|Element" ui/core/model/`.
3. Create `ui/core/dom-renderer.js`. It imports the model and owns all
   element creation. Move the DOM parts of `render.js` and `layout.js` there.
4. Add `ui/core/model/test.mjs`: a Node or Deno script that imports the
   model, builds a tree of 3 000 nodes, sorts, folds and formats a deep link.
   Run it with `node ui/core/model/test.mjs`.

## Done when

- The grep in step 2 prints nothing.
- `node ui/core/model/test.mjs` exits with 0.
- All static tests and server tests pass.

## Scope

`ui/core/`.
