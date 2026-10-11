# ADR 0021: Horizontal scroll = fold dial, not translation

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

Horizontal scroll = fold dial, not translation

## Measurement

`#stage` is sticky so nothing moves; `scrollLeft` is read as 0–100 %. Keeps the preview readable with no manual splitter

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.

Superseded in part on 2026-10-11 by [ADR 0075]: the dial is still a fold
control, but the scrollbar spans one stop each way and the axis extends left
of natural, where columns widen.

[ADR 0075]: 0075-the-scrollbar-spans-one-stop-each-way.md
