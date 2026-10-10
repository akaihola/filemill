# ADR 0074: The status strip drops whole hints, never wraps or clips

Date: 2026-10-10

## Context

`#status` is a 24 px flex row with `overflow: hidden`. When its items did not fit
— at 838 px wide, the README screencast's viewport, with columns folded — they
shrank and their text wrapped: "4/5 folded" and the label after each `<kbd>`
broke onto a second line that the strip's height cut off. Only portrait phones
hid the hints, and they hid all of them at once ([88]).

## Decision

No status item shrinks or wraps its text. The strip is `flex-wrap: wrap` with
`align-content: flex-start`, every item is as tall as the strip, and the strip's
fixed height hides the second row whole. The hints come last in the markup, in
priority order, so they are what wraps — lowest priority first, from the end —
and the path, messages and fold count stay on the visible row. `#st-path` and
`#st-copy` keep shrinking with an ellipsis, as before, for the case where the
row overflows with no hint left to drop.

Layout does the dropping; no script measures the strip.

## Measurement

`test_status_bar_items_stay_on_one_line_when_hints_do_not_fit` folds four
long-named columns at 838 × 640 px and checks that every status item with text
is no taller than the strip and sits either wholly inside it or wholly outside
it, that the fold count is shown, and that at least one hint survives.

## Consequences

A hint that does not fit is absent, not squeezed. Hidden hints stay in the DOM,
so assistive technology still reads them. Reordering hints in `ui/core/shell.js`
changes which ones drop first.

[88]: ../tasks/88-status-bar-hints-wrap-and-get-clipped.md
