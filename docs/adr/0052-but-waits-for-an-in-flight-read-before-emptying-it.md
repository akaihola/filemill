# ADR 0052: …but waits for an in-flight read before emptying it

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

…but waits for an in-flight read before emptying it

## Measurement

`ensureLoaded` hands a concurrent caller the *in-flight* promise. Invalidating and asking immediately therefore returns the very listing the refresh was called to replace, and looks like a refresh that silently did nothing

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
