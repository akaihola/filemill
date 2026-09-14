# ADR 0020: `pvToken` guards preview fills

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

`pvToken` guards preview fills

## Measurement

A slow read for a file you have navigated away from must not overwrite the current preview

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
