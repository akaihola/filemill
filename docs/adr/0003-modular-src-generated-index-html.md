# ADR 0003: Modular `src/`, generated `index.html`

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

Modular `src/`, generated `index.html`

## Measurement

The deliverable must be one portable file; a 1 500-line blob with 50 KB of base64 in it is not maintainable. `src/index.html` runs unbuilt, so the dev loop has no build step

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
