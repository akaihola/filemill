---
depends-on: []
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
   adds Markdown and `.docx`. The server adapter adds only the kinds the
   browser cannot read: virtual paths inside SQLite files, and `.pptx`.
4. Write one function `renderNode(node, blob)` that finds the first matching
   entry, calls it, and follows `fallback` on error.
5. Add one test per entry in `static/test-ui.py`.

## Notes from the original implementation

- `render(node, blob)` returns an HTML string, not an element, to match the
  `PREVIEW` port in `ui/core/ports.js`.
- The app modules register, not the adapters. `app-fsa.js` adds the core list
  and every `preview-rich.js` entry. `app-http.js` adds the core list and only
  `.pptx`, so the server edition fetches nothing else from a CDN.

## Later changes

Task [32] subsequently moved server-edition Markdown and `.docx` into the
browser, using pinned modules from `ui/vendor/`. PPTX now uses a CDN viewer.
The registration notes above describe the registry's initial implementation;
see the current [adapter contract](../../ui/adapters/README.md).

## Done when

- `grep -n "else if" ui/adapters/preview-*.js` prints no kind selection.
- A new kind needs one entry and one test, and nothing else.

## Scope

`ui/core/renderers.js`, `ui/adapters/preview-*.js`, `static/test-ui.py`.

[6]: 6-file-kind-classification.md
[32]: 32-browser-markdown-in-server-edition.md
