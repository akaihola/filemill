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

## Clarification (2026-10-06)

"Entering a column" means moving focus to it. The history key is the chain of
folder names down to the focused column, `path[0..focusCol]`, in
`ui/core/model/deeplink.js`. Opening a folder as a preview from the focused
column does not change the key and rewrites the entry; a click in another column
or ←/→ changes it and pushes. Both editions share this rule. Issue [39] restored
it after the key had drifted to the whole open chain.

[39]: ../tasks/39-browser-history-navigation.md
