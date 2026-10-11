# ADR 0074: The status strip drops whole hints, never wraps or clips

Date: 2026-10-10

## Context

`#status` is a 24 px flex row with `overflow: hidden`. When its items did not fit
— at 838 px wide, the README screencast's viewport, with columns folded — they
shrank and their text wrapped: "4/5 folded" and the label after each `<kbd>`
broke onto a second line that the strip's height cut off. Only portrait phones
hid the hints, and they hid all of them at once ([88]).

## Decision

Status text never wraps. The main strip is a single flex row. The path and
active copy, refresh and delete messages can shrink with an ellipsis; the fold
count stays visible at its natural width.

All keyboard hints, including the fold shortcut, share a shrinkable container
after the status text. Only this container wraps and clips overflow. Every hint
is one row tall, so the container's fixed height hides later rows whole. Hints
keep their markup priority, dropping from the end first. An empty first item
ensures that even a hint wider than the remaining space moves to a hidden row
instead of being partially clipped.

Layout does the dropping; no script measures the strip.

Corrected 2026-10-11 after independent review. Wrapping the entire strip moved
long copy feedback and clipboard-refusal instructions below the visible row
before flex shrinking could shorten them. Wrapping is now confined to hints.

## Measurement

`test_status_bar_items_stay_on_one_line_when_hints_do_not_fit` folds four
long-named columns at 838 × 640, 390 × 844 and 568 × 320 px. It exercises idle
status, successful long-path copying, clipboard refusal and long delete
feedback. Every active status item and the fold count must remain inside the
strip. Only hints may be hidden, and none may be partially clipped. Idle status
at 838 px must retain some hints and drop excess hints in priority order. The
clipboard fallback must still select the full path despite display truncation.

## Consequences

A hint that does not fit is absent, not squeezed. Hidden hints stay in the DOM,
so assistive technology still reads them. Reordering hints in `ui/core/shell.js`
changes which ones drop first.

[88]: ../tasks/88-status-bar-hints-wrap-and-get-clipped.md
