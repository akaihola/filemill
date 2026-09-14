# ADR 0054: No rule in `styles.css` keys off `.col.folding` to hide chrome

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

No rule in `styles.css` keys off `.col.folding` to hide chrome

## Measurement

`folding` is **not** a transient animation state. `layout.js` sets it on column `folded`, so with nothing scrolled it sits on the *root* column permanently. A `display: none` keyed on it hid the ⟳ on the root for ever, and on whichever column the dial happened to be mid-fold on — which read as two unrelated bugs. Let the header's own opacity crossfade carry anything inside it

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
