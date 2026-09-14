# ADR 0011: The sweep runs from `render()`, over the columns in `path`

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

The sweep runs from `render()`, over the columns in `path`

## Measurement

No navigation path has to remember to ask, and nothing off screen is read. Opening one folder beside the root reads those two columns, not the tree

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
