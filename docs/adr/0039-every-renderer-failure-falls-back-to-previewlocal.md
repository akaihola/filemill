# ADR 0039: Every renderer failure falls back to `PreviewLocal`

Date: 2026-08-30

## Context

The static edition needs a documented decision for this design choice.

## Decision

Every renderer failure falls back to `PreviewLocal`

## Measurement

Offline must be a loss of fidelity, not a broken pane: raw `<pre>` with a one-line note, or nothing for a binary

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
