# ADR 0010: Sorting by name is the default and reads nothing

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

Sorting by name is the default and reads nothing

## Measurement

The listing already carries the names. Only size and mtime need the sweep, so the expensive path is entered by the option that asked for it and by nothing else

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
