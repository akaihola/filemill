# ADR 0040: Version pins on every CDN URL

Date: 2026-09-02

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
