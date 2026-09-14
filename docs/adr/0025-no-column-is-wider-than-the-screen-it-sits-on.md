# ADR 0025: No column is wider than the screen it sits on

Date: 2026-09-02

## Context

The static edition needs a documented decision for this design choice.

## Decision

No column is wider than the screen it sits on

## Measurement

`measure()`'s 380 px ceiling is a reading width, not a promise it fits: on a 375 px phone the pan could only choose which edge to lose. `render()` clamps `widths` against **`finder.clientWidth`**, and does it there rather than in `measure()` because `columnFor` caches the built column — a width measured against the old viewport would survive a rotation, while `widths` is rebuilt by every render, including the one `resize` fires

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
