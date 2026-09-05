---
depends-on: [18]
---

# Cache the preview element

## Goal

The preview is built one time per selection. A resize or a fold does not
build it again. Roadmap phase 4, step 1.

## Steps

1. Read how `colCache` in `ui/core/render.js` keys column elements.
2. Add a `previewCache` with the same shape. The key is the previewed node's
   path plus a hash of its `meta` (size and modified time).
3. In the render function, before you call `PREVIEW.render`, look up the key.
   If the element exists, reuse it. If not, render and store it.
4. Clear the entry when the file is saved from the editor, and when the user
   leaves the node.
5. In `static/test-ui.py`, add a check: count calls to `PREVIEW.render` with
   a wrapper, resize the window, and expect zero new calls.

## Done when

- The new check passes.
- The render budgets in `test-ui.py` are unchanged or better.

## Scope

`ui/core/render.js`, `static/test-ui.py`.
