# ADR 0004: Focus follows the *selection*, not the newest column

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

Focus follows the *selection*, not the newest column

## Measurement

↑/↓ must keep walking the current column even when the rows are folders. Opening a folder shows its column but does not move focus; → moves in, ← moves out

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
