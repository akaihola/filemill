# ADR 0008: `node.loading` promise, awaited by concurrent callers

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

`node.loading` promise, awaited by concurrent callers

## Measurement

Fast arrow-key navigation can hit the same directory twice before the first read finishes

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
