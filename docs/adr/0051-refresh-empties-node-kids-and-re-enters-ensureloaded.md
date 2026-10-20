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

## Adapter caches, 2026-10-21

Clearing children does not invalidate a virtual parser's source. Refresh now
also awaits the optional FS `invalidate(node)` hook before `ensureLoaded`.
[The port decision] defines this hook. JSON refresh reads the current source,
including archive members and nested columns. Selection and preview use the
existing path walk and render.

[The port decision]: 0041-core-adapters-three-ports.md#refresh-invalidation-2026-10-21
