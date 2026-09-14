# ADR 0022: The dial's resting place never folds the focused column, nor anything right of it

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

The dial's resting place never folds the focused column, nor anything right of it

## Measurement

Opening a folder is the user pointing at it, and the column to the right is what that tap produced — folding either answers the gesture by hiding its result. It is what a phone showed: at 390 px `layout()` grew its fold count until the strip and the preview fit, which took the lot. Left of focus has been walked past and may condense; a scroll, a spine click and `?layout=compressed-columns` still fold everything, because those asked for it

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
