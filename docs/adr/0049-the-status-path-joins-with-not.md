# ADR 0049: The status path joins with `/`, not ` / `

Date: 2026-08-17

## Context

The static edition needs a documented decision for this design choice.

## Decision

The status path joins with `/`, not ` / `

## Measurement

Clicking it copies it, and the refusal fallback copies the characters on screen. A display string that differs from the copied string makes the fallback quietly wrong

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
