---
depends-on: [26]
---

# Try reStructuredText rendering in the browser

## Goal

We know if `.rst` files can be rendered in the browser at an acceptable size
and load time. The result is recorded. Roadmap phase 8, step 3.

## Steps

1. Read how `ui/adapters/preview-rich.js` loads a renderer from a CDN behind
   the consent switch.
2. Add one experimental registry entry for `.rst`. Try, in this order:
   a. A JavaScript or WASM reStructuredText parser, if one exists.
   b. Pyodide with `docutils`, loaded only after consent.
3. Measure with the browser network panel: total download size in MB and
   time from first click to rendered text, on a cold cache.
4. Write `docs/adr/NNNN-rst-in-browser.md` with the measurements in
   `## Measurement`. Decide: keep the entry, or delete it.
5. If you keep it, add one test. If you delete it, delete the code in the
   same commit.

## Done when

- The ADR exists with a size and a time for each option tried.
- The tree has either a tested `.rst` entry or no `.rst` code.

## Scope

`ui/adapters/preview-rich.js`, `ui/core/renderers.js`, `docs/adr/`.
