# ADR 0060: A truncated restore is saved back truncated

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

A truncated restore is saved back truncated

## Measurement

The app remembers where the user actually is. Keeping the deeper chain would mean storing a selection that does not exist, which is the thing both features refuse to display

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
