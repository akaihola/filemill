# ADR 0024: …and when the *touched* column would overflow, the strip pans left

Date: 2026-09-02

## Context

The static edition needs a documented decision for this design choice.

## Decision

…and when the *touched* column would overflow, the strip pans left

## Measurement

The cap forbids folding past focus, so nothing else can pull that column back. Measured at 390 px with names at the width ceiling: two levels in, 292 px of a 376 px column sat inside the viewport and `#stage` clipped the rest — the row the finger had just hit, cut in half, with another 44 px lost per level below. `applyScroll` slides `#strip` by exactly the overflow and never past focus's own left edge; the ancestors leave through the left instead. The peek above survives only where focus already fits, which is every desktop width

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
