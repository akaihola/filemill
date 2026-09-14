# ADR 0061: View saves hang off `ROUTER.write`, in the adapter

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

View saves hang off `ROUTER.write`, in the adapter

## Measurement

Core already writes the location on every selection change and nowhere else, so there is nothing to add to core — and the server build has no remembered folders to hook

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
