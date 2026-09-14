# ADR 0051: Refresh empties `node.kids` and re-enters `ensureLoaded`

Date: 2026-08-17

## Context

The static edition needs a documented decision for this design choice.

## Decision

Refresh empties `node.kids` and re-enters `ensureLoaded`

## Measurement

One loading path, one debounce, one writer of `node.kids`. A separate reload call would be a second writer on the same field, and the interleaving that loses is the one nobody reproduces

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
