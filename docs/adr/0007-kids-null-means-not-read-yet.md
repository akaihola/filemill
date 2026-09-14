# ADR 0007: `kids === null` means "not read yet"

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

`kids === null` means "not read yet"

## Measurement

Distinguishes an unread directory (spinner) from an empty one ("Empty")

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
