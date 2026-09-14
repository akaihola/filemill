# ADR 0042: The chrome is built by `core/shell.js`, not written in the HTML

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

The chrome is built by `core/shell.js`, not written in the HTML

## Measurement

There are two HTML files and the markup has to match in both. A shared *file* would need a build step or a fetch, and the static build can afford neither

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
