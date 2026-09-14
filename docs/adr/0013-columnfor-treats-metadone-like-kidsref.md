# ADR 0013: `columnFor` treats `metaDone` like `kidsRef`

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

`columnFor` treats `metaDone` like `kidsRef`

## Measurement

A sweep reorders the rows, so the DOM built before it is no longer the column. Testing it there means a repaint the sweep chose to drop self-heals on the next render, instead of leaving an order that is no longer true

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
