# ADR 0040: Version pins on every CDN URL

Date: 2026-09-02

## Status update, 2026-10-19, issue [109]

The decision holds. The last paragraph below is out of date. No PowerPoint
viewer is pinned or downloaded: since `90f40ed3`, `preview-rich.js` extracts
PPTX slide text in the page. `window.FILEMILL_CDN` is not only for tests: the
server edition sets it to its vendored modules, whose pins
`ui/vendor/README.md` lists.

## Context

The static edition needs a documented decision for this design choice.

## Decision

Version pins on every CDN URL

## Measurement

`@latest` means a preview that renders differently next week, and a dependency that can change under you

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.

The pins live in the `CDN` table in `ui/adapters/preview-rich.js`. The
renderers arrive through a dynamic `import()`, which has no `integrity`
attribute, so the version pin is the reproducibility mechanism: `esm.sh` and
`cdn.jsdelivr.net` serve a versioned path as immutable content.
`pptx-vanilla-viewer@2.1.4` is pinned this way for PowerPoint files. Tests
replace a URL through `window.FILEMILL_CDN` to load a local stub instead.

[109]: ../tasks/109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md
