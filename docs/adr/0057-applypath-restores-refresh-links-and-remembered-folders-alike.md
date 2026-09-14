# ADR 0057: `applyPath` restores refresh, links and remembered folders alike

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

`applyPath` restores refresh, links and remembered folders alike

## Measurement

Three callers, one walk: they cannot disagree about what a half-valid chain means. It stops at the first name that is gone, so no caller can present a selection that is not real

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
