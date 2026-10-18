# ADR 0005: `node.lastSel` per directory

Date: 2026-08-16

## Supersession, 2026-10-19, issue [107]

Task [22] replaced this storage contract. `ui/core/model/selection.js` stores
selected names in `sel[i]`; `ui/core/model/state.js:rowIndex` derives row
indices. Current source has no `node.lastSel`. Do not restore that field to
satisfy the original decision. Its decision and measurement below are the
historical contract; current selection behavior is defined by the model and
its tests in `ui/core/model/test.mjs`.

## Context

The static edition needs a documented decision for this design choice.

## Decision

`node.lastSel` per directory

## Measurement

→ returns to the row you were on last time you were in that column, instead of always the first

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
