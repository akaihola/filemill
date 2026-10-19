# ADR 0025: No column is wider than the screen it sits on

Date: 2026-09-02

## Partial supersession, 2026-10-19, issue [109]

The decision still holds, through other code. `measure()` and its 380 px
ceiling are gone, and `render()` no longer clamps `widths`. Since `fe3a2306`,
`folderWidth()` in `ui/core/dom-renderer.js` gives every folder column one
width: `20em` on a desktop, or a share of the finder's width on a phone. See
[ADR 0062](0062-narrow-screen-layout-model.md).

## Context

The static edition needs a documented decision for this design choice.

## Decision

No column is wider than the screen it sits on

## Measurement

`measure()`'s 380 px ceiling is a reading width, not a promise it fits: on a 375 px phone the pan could only choose which edge to lose. `render()` clamps `widths` against **`finder.clientWidth`**, and does it there rather than in `measure()` because `columnFor` caches the built column — a width measured against the old viewport would survive a rotation, while `widths` is rebuilt by every render, including the one `resize` fires

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.

[109]: ../tasks/109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md
