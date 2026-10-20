# ADR 0084: A wheel gesture keeps the axis it started on

Date: 2026-10-19

## Context

Fingers scrolling a document up and down on a touchpad drift sideways now
and then, so some wheel events of a vertical swipe carry a horizontal delta,
and a few are mostly horizontal. [ADR 0076] judged every wheel over the
preview on its own: one mostly horizontal event in the middle of a vertical
swipe turned the dial, and the column layout changed under the reader
([110]). The browser adds its own cases. It latches a gesture to the first
scroller that can take any part of its first delta, so a downward swipe at
the end of a document or a column list, or over one that does not scroll,
goes to `#finder` and its drift turns the dial. A sideways swipe over the
preview lost the horizontal part of its mostly vertical events and scrolled
the document instead.

## Decision

A wheel gesture takes an axis once it has travelled `AXIS_SLOP` (6 px) along
either axis: horizontal if it went further sideways, vertical otherwise, so
a diagonal start reads as scrolling. Until then its events are prevented and
go nowhere, because the first events of a swipe are small and noisy, and
the browser would latch them to a scroller of its own choosing. The gesture
ends as in [ADR 0076], when the dial settles (`SETTLE_MS` without scroll,
wheel or touchmove). A Ctrl+wheel, which is how a touchpad pinch arrives,
zooms and is left to the browser.

The `wheel` listener on `#finder` treats every other event of the gesture by
its axis:

- An event with no delta across the axis goes to the browser, unchanged.
- In a horizontal gesture over the preview, the dial takes a cancellable
  event while [ADR 0076] gives the dial the gesture, whatever the event's own
  direction.
- An event that drifts across the axis is prevented if it can still be
  cancelled. Its delta along the axis scrolls the innermost scroller under
  the pointer that can still move that way, up to `#finder`, which is the
  dial. In fullscreen the search stops at `#preview`. There the preview fills
  the screen, and the dial behind it must not turn.
- An event that can no longer be cancelled is left alone. A browser that has
  begun scrolling a gesture natively may send the rest of it uncancellable to
  the scroller it latched. Filemill adds nothing to such an event and never
  turns the dial from a vertical gesture.

The listener is on `#finder`, so a swipe over a column list keeps its axis
as well.

## Measurement

The browser tests open `code/long.py` with the dial at natural and wheel
over the document. Each swipe records the gaps between its wheels, and the
assertions after it report them: on a busy machine a gap past `SETTLE_MS`
ends the gesture early.

- `test_a_vertical_swipe_over_the_preview_ignores_sideways_drift` wheels
  `(0, 40)`, `(6, 3)`, `(4, 30)` and `(0, 40)`: the document scrolls and the
  dial stays at 0. Before the change the `(6, 3)` event turned it 6 px. The
  test then scrolls the document to its end and wheels `(3, 40)`, `(0, 40)`
  and `(5, 2)`. Before the change the browser gave the first event's 3 px to
  the finder and Filemill gave it the last one's 5 px.
- `test_a_sideways_swipe_over_the_preview_ignores_vertical_drift` wheels
  `(40, 0)`, `(30, 4)`, `(3, 6)`, `(0, 20)` and `(20, 0)` over a light
  Markdown document. `code/long.py` was too heavy here: each wheel turns the
  dial and lays the preview out again, and on a loaded machine that held the
  next wheel past `SETTLE_MS`. The dial turns 93 px, the sum of the
  horizontal deltas, and the document does not scroll. Before the change the
  `(3, 6)` event was left to the browser, and the dial ended at 90 px.
- `test_a_vertical_swipe_over_a_column_ignores_sideways_drift` repeats the
  vertical swipes over the 20 000-line listing of `big.jsonl`. Its first
  swipe passed before the change, because the browser latched the list. At
  the end of the list the dial turned 8 px.
- `test_a_swipe_takes_its_axis_after_a_few_pixels` starts a vertical swipe
  with `(1, 0)` and `(2, 1)`. Fixing the axis from the first event alone gave
  the whole swipe to the dial, and the document never scrolled.
- `test_a_pinch_over_the_preview_is_left_to_the_browser` dispatches a
  sideways Ctrl+wheel over the wide code block of `wide.md`. Before, the dial
  took it.

`test_fullscreen_releases_a_latched_preview_wheel` now wheels 10 px instead of
1 px, past the slop, so that its first wheel still latches the dial. The other
tests of [ADR 0075] and [ADR 0076] still pass. Their wheels move along one
axis, far past the slop.

## Consequences

The first 6 px of each touchpad gesture are dropped. A mouse wheel moves at
least a line at a time, so it takes its axis on the first event. A deliberate
change of direction within a gesture waits for the gesture to end, as it does
when the browser latches a scroller. Filemill scrolls the drifting events it
prevents instantly, with no smooth-scroll animation. Touchpads send them in
pixels, and a mouse wheel moves along one axis, so its events stay with the
browser. The headless tests send every wheel cancellable, so they cover the
prevented path. The uncancellable path is the browser's own latching.

[ADR 0075]: 0075-the-scrollbar-spans-one-stop-each-way.md
[ADR 0076]: 0076-a-sideways-wheel-over-the-preview-turns-the-dial-first.md
[110]: ../tasks/110-confusing-diagonal-scroll.md
