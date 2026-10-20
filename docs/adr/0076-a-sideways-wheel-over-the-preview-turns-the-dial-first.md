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

Fullscreen is an exception, clarified after independent review on 2026-10-11.
Both native fullscreen and its layout fallback already fill the screen,
regardless of the dial position. Their scrollers receive horizontal wheels
immediately. The fullscreen check runs before the gesture latch, so entering
fullscreen during a gesture releases that gesture to the preview too.

The `wheel` listener on `#finder` is therefore no longer passive; `touchmove`
still is. `deltaMode` lines count 40 px and pages the finder's width.

## Measurement

`test_a_sideways_wheel_over_a_wide_preview_turns_the_dial_first` opens
`wide.md` at natural, wheels over the code block and checks that the dial moved
and the block did not, then moves the dial to its end and checks that the next
wheel scrolls the block and leaves the dial where it was. The fling and
slow-scroll tests of [ADR 0075] still pass with the shared listener.

The fullscreen regression opens the same wide block with the dial at natural
and checks that the first sideways wheel scrolls the block without moving the
dial, in both native and fallback modes. A second regression enters fullscreen
during a latched gesture and checks that the next wheel is not prevented.

## Consequences

Vertical and mostly vertical wheels are untouched, so reading a document
scrolls it as before. A block that was scrolled sideways keeps its offset when
the dial leaves the end; it scrolls back once the dial is at the end again,
which the same gesture reaches first.

Refined 2026-10-19 by [ADR 0084] ([110]): a wheel is judged by the axis
its gesture took in its first few pixels, not by its own deltas. A mostly
horizontal event inside a vertical swipe no longer turns the dial. While the
dial takes a sideways gesture over the preview, short of its end, it takes
every cancellable event of that gesture.

[ADR 0021]: 0021-horizontal-scroll-fold-dial-not-translation.md
[ADR 0075]: 0075-the-scrollbar-spans-one-stop-each-way.md
[78]: ../tasks/78-wide-document-scrolls-instead-of-expanding-the-preview.md
[ADR 0084]: 0084-a-wheel-gesture-keeps-the-axis-it-started-on.md
[110]: ../tasks/110-confusing-diagonal-scroll.md
