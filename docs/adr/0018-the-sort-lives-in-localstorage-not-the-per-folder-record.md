# ADR 0018: The sort lives in `localStorage`, not the per-folder record

Date: 2026-08-19

## Context

The static edition needs a documented decision for this design choice.

## Decision

The sort lives in `localStorage`, not the per-folder record

## Measurement

It is how a person reads a list, not a property of the folder. The record also offers no hook: `keepView` fires from `ROUTER.write`, which core calls when the *location* changes, and choosing a sort moves nobody

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
