# ADR 0038: A text preview is whole or absent; `TEXT_MAX` (512 KB) is the only limit

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

A text preview is whole or absent; `TEXT_MAX` (512 KB) is the only limit

## Measurement

Colouring the full 512 KB costs 22 ms of regex and 273 ms of DOM in Chromium — once, on the click that asked for it, against 140 ms for the same text uncoloured. So a second "colour budget" tier below the read gate would buy ~130 ms and cost a rule: the DOM is the price, not the colour. Slicing on scroll was rejected outright — a triple-quoted string or a block comment spanning the cut mis-tokenises, and `syntax.js` promises every character exactly once. The old 8 000-character clip was none of these: it truncated the file with no limit anyone could predict from its size

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
