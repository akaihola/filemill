# ADR 0037: Syntax highlighting in the page (`core/syntax.js`), not from Pygments or a CDN

Date: 2026-08-30

## Context

The static edition needs a documented decision for this design choice.

## Decision

Syntax highlighting in the page (`core/syntax.js`), not from Pygments or a CDN

## Measurement

One implementation colours source in both builds, offline, in either theme — a server-rendered version would have to be written twice, and the CDN highlighter's stylesheet is light-theme only

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
