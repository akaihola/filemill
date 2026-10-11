# ADR 0029: Column DOM cached per `(node, kids)` in `colCache`

Date: 2026-09-02

## Context

The static edition needs a documented decision for this design choice.

## Decision

Column DOM cached per `(node, kids)` in `colCache`

## Measurement

Rebuilding a 3 000-entry column per keystroke cost ~500 ms. Re-renders re-apply
depth/selection/cursor classes. Since 2026-10-11 they also remove a cached row's
chevron when an adapter declines the entry and turns it into a leaf, without
rebuilding the column ([84](../tasks/84-json-member-in-archive-shows-chevron-but-does-not-open.md)).

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
