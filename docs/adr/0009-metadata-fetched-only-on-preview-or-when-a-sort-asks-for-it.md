# ADR 0009: Metadata fetched only on preview, or when a sort asks for it

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

Metadata fetched only on preview, or when a sort asks for it

## Measurement

`getFile()` is a syscall per file: 284 µs each, 851 ms for 3 000 of them, measured against a real filesystem in `test-url.py`. Per row on every open it would stall large directories

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
