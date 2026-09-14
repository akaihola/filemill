# ADR 0033: Click handler on `.col`, not just rows

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

Click handler on `.col`, not just rows

## Measurement

A folded column hides its rows, so "click a spine to unfold" must be handled by the column (the design study advertised this but never wired it)

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
