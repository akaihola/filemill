# ADR 0032: `content-visibility: auto` on `.row`

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

`content-visibility: auto` on `.row`

## Measurement

Rows have a fixed height, so off-screen ones are skipped: forced layouts (`scrollIntoView`) stop being O(entries)

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
