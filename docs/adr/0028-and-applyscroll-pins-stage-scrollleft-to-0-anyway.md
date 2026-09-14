# ADR 0028: …and `applyScroll` pins `stage.scrollLeft` to 0 anyway

Date: 2026-09-02

## Context

The static edition needs a documented decision for this design choice.

## Decision

…and `applyScroll` pins `stage.scrollLeft` to 0 anyway

## Measurement

`overflow: hidden` stops a finger, not a programmatic scroll, and the app is not the only thing that makes them — a browser bringing a focused element into view, a test harness centring a row. `revealRow` stops ours; this undoes everyone else's at the next repaint

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
