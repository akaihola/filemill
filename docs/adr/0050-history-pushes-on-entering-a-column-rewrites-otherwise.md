# ADR 0050: History pushes on entering a column, rewrites otherwise

Date: 2026-08-17

## Context

The static edition needs this design choice documented.

## Decision

History pushes on entering a column, rewrites otherwise

## Measurement

Selecting folders opens columns without moving focus; ↑/↓ would otherwise push
one history entry per row and make Back useless

## Consequences

The static edition follows this decision; the measurement guides maintenance and evaluation.

## Clarification (2026-10-07)

The history key is the open directory chain, `path.map(name)`, in `ui/core/model/deeplink.js`.
Clicking another folder changes the chain and pushes; choosing a file in the open folder rewrites. Keyboard stepping
with ↑/↓, Home/End, PageUp/PageDown sets `state.stepping` through `choose()` and
always rewrites, however many folders open, as measured above. Both editions share
this rule, restored by issue [39] after ↑/↓ over folders pushed one entry per row.

## Loading columns (2026-10-21)

Only settled open chains supply history keys. URL synchronization waits, with loading
UI visible, while a column is unread or declined by its adapter but not yet removed
by navigation. Once read, confirmed outlines push; plain files rewrite their containing
folder's entry. Read timing must not change Back's sequence. [The Back race]
records the reproduction and controlled-response regression.

[39]: ../tasks/39-browser-history-navigation.md
[The Back race]: ../tasks/137-fix-the-intermittent-back-failure-in-test-back-retraces-the-folders-th.md
