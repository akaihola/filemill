# ADR 0027: `revealRow` scrolls the column body, never `scrollIntoView`

Date: 2026-09-02

## Context

The static edition needs a documented decision for this design choice.

## Decision

`revealRow` scrolls the column body, never `scrollIntoView`

## Measurement

Once the strip may be wider than the stage, the obvious call is the wrong one: it scrolls whichever ancestor reveals the row, and that ancestor is `#stage`. Permanently — the dial writes `#finder`, and nothing writes `#stage` back. Measured at 320 px: the strip dragged 114 px out through the left edge and stayed there. A row needs one axis, and it is vertical

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
