# ADR 0048: A refused clipboard selects the path instead

Date: 2026-08-17

## Context

The static edition needs a documented decision for this design choice.

## Decision

A refused clipboard selects the path instead

## Measurement

`writeText` can be refused by policy or context. Failing silently means the next paste hands over something else with nothing to say so; selecting the path puts the browser's own ⌘C one keystroke away, and that one needs no permission

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
