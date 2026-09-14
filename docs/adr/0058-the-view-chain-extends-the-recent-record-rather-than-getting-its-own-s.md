# ADR 0058: The view chain extends the `recent` record, rather than getting its own store

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

The view chain extends the `recent` record, rather than getting its own store

## Measurement

A handle is not a path, so the only honest key for a per-folder store is the handle already sitting in this record. Two stores would also drift the first time one is pruned to 8 and the other is not

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
