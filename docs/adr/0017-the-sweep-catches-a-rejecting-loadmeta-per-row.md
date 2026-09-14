# ADR 0017: The sweep catches a rejecting `loadMeta` per row

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

The sweep catches a rejecting `loadMeta` per row

## Measurement

The port promises to *fill* `node.meta`, not that it never rejects. One escaping rejection would leave `metaLoading` set for good and the column spinning until the tab closed

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
