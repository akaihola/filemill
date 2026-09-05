---
depends-on: [19]
---

# One renderer registry

## Goal

Adding a preview kind is one entry in one table plus one test. Both editions
use the same table. Roadmap phase 8, step 1.

## Steps

1. Create `ui/core/renderers.js`. Export a list `RENDERERS` of objects
   `{kind, render, fallback}`. `kind` is a string from the file-kind rule of
   task [6]. `render(node, blob)` returns an element or throws. `fallback`
   is the `kind` to use when `render` throws.
2. Move the current `if`/`else` chain in the preview code into entries of
   that list. Start with text, image, PDF, Markdown, JSON.
3. Each adapter appends its own entries to the list at boot. `preview-rich.js`
   adds the CDN renderers. The server adapter adds the server-rendered kinds.
4. Write one function `renderNode(node, blob)` that finds the first matching
   entry, calls it, and follows `fallback` on error.
5. Add one test per entry in `static/test-ui.py`.

## Done when

- `grep -n "else if" ui/adapters/preview-*.js` prints no kind selection.
- A new kind needs one entry and one test, and nothing else.

## Scope

`ui/core/renderers.js`, `ui/adapters/preview-*.js`, `static/test-ui.py`.
