# ADR 0016: Directories are never ordered by size or time

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

Directories are never ordered by size or time

## Measurement

No port can give a directory either number: there is no `getFile()` for a directory handle, and the server build's listing sends metadata for files only

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
