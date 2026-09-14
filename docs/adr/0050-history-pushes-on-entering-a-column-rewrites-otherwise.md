# ADR 0050: History pushes on entering a column, rewrites otherwise

Date: 2026-08-17

## Context

The static edition needs a documented decision for this design choice.

## Decision

History pushes on entering a column, rewrites otherwise

## Measurement

Selecting a folder opens its column without moving focus, so ↑/↓ down a list of folders would otherwise push a history entry per row and make Back useless

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
