# ADR 0015: Unreadable metadata sorts last in **both** directions

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

Unreadable metadata sorts last in **both** directions

## Measurement

"Biggest first" asks what is biggest; a file the app could not open is not the answer, and putting one at the top is how a permission error gets read as a result. The row is never dropped

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
