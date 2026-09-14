# ADR 0046: Only the matched row gets `<mark>`

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

Only the matched row gets `<mark>`

## Measurement

Marking every matching row is an innerHTML write per entry — the O(entries)-per-keystroke cost the column cache exists to avoid. One row is also the honest signal: type-ahead jumps to one place

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
