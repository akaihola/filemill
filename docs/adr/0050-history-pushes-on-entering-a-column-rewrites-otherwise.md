# ADR 0050: History pushes on entering a column, rewrites otherwise

Date: 2026-08-17

## Context

The static edition needs a documented decision for this design choice.

## Decision

History pushes on entering a column, rewrites otherwise

## Measurement

Selecting a folder opens its column without moving focus, so ↑/↓ down a list of
folders would otherwise push a history entry per row and make Back useless

## Consequences

The static edition follows this decision. The measurement above records the
basis for maintaining and evaluating it.

## Clarification (2026-10-07)

The history key is the open directory chain, `path.map(name)`, in
`ui/core/model/deeplink.js`. A click that opens another folder changes the chain
and pushes; choosing a file inside the open folder rewrites. Keyboard stepping
with ↑/↓, Home/End, PageUp/PageDown sets `state.stepping` through `choose()` and
always rewrites, however many folders the walk opens, which is the measurement
above. Both editions share this rule. Issue [39] restored it after ↑/↓ over
folders had started pushing one entry per row.

[39]: ../tasks/39-browser-history-navigation.md
