# ADR 0023: …so a column right of focus may overflow the finder, and only its left edge is promised

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

…so a column right of focus may overflow the finder, and only its left edge is promised

## Measurement

271 px of root plus 176 of the folder it opens is 467 on a 390 px screen: something has to leave, and the choice is that it will not be the column under the finger. The peek that remains is the affordance saying the strip scrolls (ISSUES.md #43)

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
