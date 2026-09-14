# ADR 0056: Refreshing a parent re-reads the columns open below it

Date: 2026-08-19

## Context

The static edition needs a documented decision for this design choice.

## Decision

Refreshing a parent re-reads the columns open below it

## Measurement

A re-read hands back new node objects, so the chain has to be matched by name regardless. Those columns are also on screen, and one fresh column beside three stale ones is worse than the extra reads. Closed subtrees are untouched

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
