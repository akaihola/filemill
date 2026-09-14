# ADR 0012: `ensureMeta` mirrors `FS.ensureLoaded`

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

`ensureMeta` mirrors `FS.ensureLoaded`

## Measurement

One in-flight promise on the node, one writer of the field, so a second render joins the sweep running instead of starting a rival — the same reason `node.loading` exists

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
