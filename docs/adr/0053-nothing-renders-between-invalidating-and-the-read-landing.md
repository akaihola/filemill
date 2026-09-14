# ADR 0053: Nothing renders between invalidating and the read landing

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

Nothing renders between invalidating and the read landing

## Measurement

The column cache still holds the old DOM, so the screen keeps the previous listing instead of flashing to "Reading…" and losing its scroll position. The ⟳ spins in place instead

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
