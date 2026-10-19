# ADR 0003: Modular `src/`, generated `index.html`

Date: 2026-08-16

## Path update, 2026-10-19, issue [109]

The decision still holds. The modules no longer live in `src/`: they are the
shared `ui/` tree, a symlink to `server/src/filemill/ui/` (`d10c714e`,
`e01a40b4`). `static/index-dev.html` loads them unbuilt, and
`static/build-index.py` writes `static/index.html`.

## Context

The static edition needs a documented decision for this design choice.

## Decision

Modular `src/`, generated `index.html`

## Measurement

The deliverable must be one portable file; a 1 500-line blob with 50 KB of base64 in it is not maintainable. `src/index.html` runs unbuilt, so the dev loop has no build step

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.

[109]: ../tasks/109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md
