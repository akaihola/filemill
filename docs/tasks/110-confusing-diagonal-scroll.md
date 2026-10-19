Often when I scroll the preview pane up and down on a touchpad, my fingers move slightly horizontally as well, causing the column layout to change. Lock the scroll to happen only along the initial axis of the scroll gesture.

## Cause

`ui/core/layout.js` judged each wheel over the preview on its own deltas
([ADR 0076]): any event with `|deltaX| ≥ |deltaY|` turned the fold dial. A
vertical touchpad swipe that drifts sideways sends a few such events, and each
one moved the columns. The browser adds two more cases. A downward swipe at
the end of a document or a column list, or over one that does not scroll,
latches to `#finder` because only the finder can take part of the delta, and
the drift turns the dial. A sideways swipe over the preview left its mostly
vertical events to the browser, which scrolled the document and dropped their
horizontal part.

## Plan

- Red: browser tests in `server/tests/test_browser_new_ui.py` wheel over
  `code/long.py` with the dial at natural. A vertical swipe with sideways drift
  must leave the dial at 0, also after the document is scrolled to its end. A
  sideways swipe with vertical drift must turn the dial by the sum of its
  horizontal deltas and leave the document unscrolled. The vertical swipes
  repeat over a column list.
- Green: a gesture takes its axis after `AXIS_SLOP` pixels of travel and keeps
  it until the dial settles, as the [ADR 0076] latch does. Events along the
  axis stay with the browser. A cancellable event that drifts across it is
  prevented, and its delta along the axis scrolls the innermost scroller that
  can still move that way. The search stops at `#finder`, or at `#preview` in
  fullscreen. In a sideways gesture over the preview the dial takes every
  cancellable event while [ADR 0076] gives it the gesture. Ctrl+wheel (pinch)
  stays with the browser.
- [ADR 0084] records the decision; [ADR 0076] and
  `docs/ARCHITECTURE-REVIEW.md` note the refinement. Rebuild
  `static/index.html`.

## Validation, 2026-10-19

Before the change, the vertical preview swipe turned the dial 6 px, and 8 px
at the end of the document. The sideways swipe ended at 90 px instead of
93 px. Over the column list the first swipe passed, because the browser
latched the list, but at the end of the list the dial turned 8 px.

An independent review of the first version found five problems:

- Fixing the axis from the first event alone gave a whole swipe to the dial
  when the swipe started with a sideways-leaning event.
- The dial took events that could no longer be cancelled.
- The scroller search ignored direction.
- Ctrl+wheel went through the axis logic.
- A slow machine could split a test swipe without saying so.

Two further tests cover the first and fourth problems:
`test_a_swipe_takes_its_axis_after_a_few_pixels` and
`test_a_pinch_over_the_preview_is_left_to_the_browser`. Both failed against
the first version: the document never scrolled, and the pinch was prevented
and turned the dial 20 px. The swipe helper now returns the gaps between its
wheel events, and the assertions after a swipe report them. The sideways test
moved from `code/long.py` to a light Markdown document in a private tree:
re-laying out `long.py` for each dial move held the next wheel up to 283 ms
on the loaded host and split the swipe.
`test_fullscreen_releases_a_latched_preview_wheel` wheels 10 px instead of
1 px, past the slop.

[ADR 0076]: ../adr/0076-a-sideways-wheel-over-the-preview-turns-the-dial-first.md
[ADR 0084]: ../adr/0084-a-wheel-gesture-keeps-the-axis-it-started-on.md
