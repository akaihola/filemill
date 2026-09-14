# ADR 0035: Rich renderers lazy-loaded from a CDN, not bundled

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

Rich renderers lazy-loaded from a CDN, not bundled

## Measurement

markdown-it + plugins + mammoth are ~1 MB against the app's 140 KB. Fetching them on first use keeps the single file portable and gives it filemill's rendering

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
