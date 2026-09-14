# ADR 0026: …measured on `#finder`, never on `#stage`

Date: 2026-09-02

## Context

The static edition needs a documented decision for this design choice.

## Decision

…measured on `#finder`, never on `#stage`

## Measurement

The stage is one render behind: its width is `--stage-w`, which `layout()` writes *after* `render()` has already chosen the widths. Clamping against it measured the viewport the user had just rotated away from — from 568 px landscape to 375 px portrait that kept 380 px columns on a 375 px screen, and the tapped row sat 10 px past the right edge until the next render healed it. `#finder` is `flex: 1` in the viewport, so it is the live number, and it is the one `layout()` reads to set `--stage-w` in the first place

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
