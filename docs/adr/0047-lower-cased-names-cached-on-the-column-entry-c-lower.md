# ADR 0047: Lower-cased names cached on the column entry (`c.lower`)

Date: 2026-08-17

## Context

The static edition needs a documented decision for this design choice.

## Decision

Lower-cased names cached on the column entry (`c.lower`)

## Measurement

Lower-casing 3 000 names costs ~1.4 ms; per keystroke that is most of the search budget. Cached beside `c.kids`, so the two die together and can never disagree

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
