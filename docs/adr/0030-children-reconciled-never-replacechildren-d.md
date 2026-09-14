# ADR 0030: Children reconciled, never `replaceChildren`d

Date: 2026-09-02

## Context

The static edition needs a documented decision for this design choice.

## Decision

Children reconciled, never `replaceChildren`d

## Measurement

Re-inserting an element detaches it and discards the style + layout of every row under it — that alone was the 500 ms

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
