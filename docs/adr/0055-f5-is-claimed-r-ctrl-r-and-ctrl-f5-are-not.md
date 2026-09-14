# ADR 0055: F5 is claimed; ⌘R, Ctrl+R and Ctrl+F5 are not

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

F5 is claimed; ⌘R, Ctrl+R and Ctrl+F5 are not

## Measurement

Every desktop file manager reads F5 as "re-read this folder", and here a reload costs the mounted root, the column chain and the scroll position. A real reload stays one keystroke away — the rule type-ahead already follows for ⌘R

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
