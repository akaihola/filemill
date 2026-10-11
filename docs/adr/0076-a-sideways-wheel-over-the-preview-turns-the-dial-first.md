# ADR 0076: A sideways wheel over the preview turns the dial first

Date: 2026-10-11

## Context

`#preview .pv-body` and a rendered code block (`.pv-rich pre`) are
`overflow: auto` scroll containers nested inside `#finder`, the fold dial
([ADR 0021], [ADR 0075]). A browser gives a horizontal wheel to the innermost
element that can scroll along that axis, so over a document with a wide code
block a trackpad swipe scrolled the block and never reached the dial, while over
a narrow document the same swipe chained up to the finder and widened the
preview ([78]).

## Decision

A mostly horizontal wheel (`|deltaX| ≥ |deltaY|`) whose target is inside
`#preview` is taken by the dial while the dial is short of its end: the event is
prevented and its delta is applied to the finder's own scroll, so folds, stops
and settling behave as for a wheel over the columns. At the end of the dial the
preview is as wide as the screen allows, and the preview's own scrollers take
the gesture.

A gesture latches to the dial the way a browser latches a gesture to one
scroller: once the dial has taken a wheel, every wheel until the dial settles
(`SETTLE_MS` without scroll, wheel or touchmove) stays with it, so a fling that
reaches the end does not run on into the code block. The next gesture scrolls
the block.

The `wheel` listener on `#finder` is therefore no longer passive; `touchmove`
still is. `deltaMode` lines count 40 px and pages the finder's width.

## Measurement

`test_a_sideways_wheel_over_a_wide_preview_turns_the_dial_first` opens
`wide.md` at natural, wheels over the code block and checks that the dial moved
and the block did not, then moves the dial to its end and checks that the next
wheel scrolls the block and leaves the dial where it was. The fling and
slow-scroll tests of [ADR 0075] still pass with the shared listener.

## Consequences

Vertical and mostly vertical wheels are untouched, so reading a document
scrolls it as before. A block that was scrolled sideways keeps its offset when
the dial leaves the end; it scrolls back once the dial is at the end again,
which the same gesture reaches first.

[ADR 0021]: 0021-horizontal-scroll-fold-dial-not-translation.md
[ADR 0075]: 0075-the-scrollbar-spans-one-stop-each-way.md
