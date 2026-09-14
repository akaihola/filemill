# ADR 0045: Type-ahead rungs are three passes, not one scored scan

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

Type-ahead rungs are three passes, not one scored scan

## Measurement

The rungs have to rank across the *whole* column: a name starting with "notes" on row 300 must beat one containing it on row 3. Each pass stops at its own first hit, so an early prefix match never looks at the rest

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
