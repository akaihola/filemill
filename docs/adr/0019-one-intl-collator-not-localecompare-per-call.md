# ADR 0019: One `Intl.Collator`, not `localeCompare` per call

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

One `Intl.Collator`, not `localeCompare` per call

## Measurement

The comparator runs ~35 000 times per column build at 3 000 entries. Reusing it took ordering 3 000 real files from 116.6 ms to 18.2 ms

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
