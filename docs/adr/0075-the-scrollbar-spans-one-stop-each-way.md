# ADR 0075: The scrollbar spans one dial stop each way

Date: 2026-10-11

## Context

[ADR 0021] made horizontal scroll a fold dial: `#finder` scrolls over a rail as
wide as every column, and the position is read as 0–100 %. A fast touchpad
swipe runs the scrollbar to its end, which is all columns unfolded on the left
and the preview alone on the right. Nothing in between was reachable by a fling,
and nothing wider than natural existed at all ([81]).

## Decision

The dial is one axis in pixels. Right of natural it is the old dial: `k × unit`
folds `k` columns, `n × unit` (99 %) folds all `n`, `range` slides the spines
away. Left of natural, new, the leftmost columns widen so that fewer of them fill
the finder: one fewer than fit beside the preview reserve, then one fewer again,
down to two columns, or to one where fewer than two fit (a portrait phone). The
columns shown are always the leftmost; the focus pan fades out over the first
widening unit.

The stops are: each widened count, natural, the rightmost column whole over
spines (`n − 1` folded), all folded, the preview alone.

The scrollbar spans the two stops either side of the dial — the neighbours of
the stop it rests on, or the pair enclosing it in between — so a fling clamps at
the next stop. When the dial has been still for `SETTLE_MS` (180 ms) with no
scroll, wheel or touchmove event and no mouse button or finger held on the
finder, the range is re-based around the new stop: the rail width and
`scrollLeft` change together and nothing on screen moves. Programmatic moves
(`layout`, → in the preview, a spine click) go through `dialTo`, which widens
the range to hold both ends of a move and lets settling narrow it again.

A tap rests the dial as before ([ADR 0022]); at a widened stop that means the
nearest widened stop that still shows the focused column and the one it opened,
natural at the latest. Vertical navigation keeps a widened stop the way it keeps
a deliberate fold.

`#finder` has `overscroll-behavior-x: contain`, so a fling that ends on a stop
does not become the browser's back or forward gesture.

The arithmetic is `fitCount`, `wideCounts`, `dialStops`, `dialWindow` and
`widenedSizes` in `ui/core/model/folding.js`; `ui/core/layout.js` owns `base`,
`dial()`, `dialTo()` and the settle timer. Tests read the dial through `dial()`,
never `scrollLeft`, which is scrollbar-relative.

## Measurement

Model tests cover the stop lists for one, two and four columns on a laptop and
a phone, the ranges at, between and at the ends of the stops, and widened sizes
at and between stops. `test_flings_stop_at_each_fold_stop` sends wheel flings
far past any stop and checks each landing in both directions at 1500 × 900,
including that a desktop never widens to one column and that the ends hold.
Further browser tests cover a slow scroll between widening stops, → from a
widened stop, a spine click from fully folded across ranges, and a phone tap
that opens a folder from a full-width root.

### Independent-review corrections, 2026-10-11

Widening counts can change on resize even when column width and path length
stay fixed. Layout detects that change and remaps a whole widened stop to the
same column count where available. Partial positions outside the new range are
clamped before rebasing. Changing only the widening counts retains that widened
position instead of applying the automatic fold for the focused column. Widened
counts use the same 0.5 px stop tolerance as folding, so a rounded landing is
not mistaken for the next wider stop.

The base absorbs the rounding needed to preserve the current dial position.
The rail span is the rounded distance from that adjusted base to the upper
stop, keeping both native scroll endpoints within 0.5 px of their stops.
Sizing it from the original interval could miss the upper stop and consume an
extra fling, reproduced at 414 px with a first landing of 429 instead of 429.66.

Browser regressions cover 1500 ↔ 1000 px resizing, an out-of-range partial
widening, and repeated flings in both directions at 413 and 414 px and with
fractional desktop column widths. A four-column path resized from 1500 to
2000 px keeps three widened columns after a rounded native landing.

## Consequences

`finder.scrollLeft` no longer equals the dial position; tests that read it as
the dial were changed to `dial()`. A fling takes three swipes from natural to
the preview alone where it took one. The scrollbar thumb is now a stop-relative
indicator, not a position over the whole axis.

Three timing rules came out of the browser suites. The rail is
`calc(100% + range)`, because a pixel width set from the finder let a resize
shrink the range and Chrome clamped `scrollLeft` while `base` stayed. A glide
takes no explicit behaviour, so the stylesheet decides, and a glide issued in
the same frame as an instant scroll write waits a frame, because the write cut
it in mobile emulation. The long-press timer in `render.js` was shared by every
row and any row's pointerleave cleared it; a fold glide moving rows under a
resting mouse ended a finger's press elsewhere, so only the pointer that
started a press may end it.

[ADR 0021]: 0021-horizontal-scroll-fold-dial-not-translation.md
[ADR 0022]: 0022-the-dial-s-resting-place-never-folds-the-focused-column-nor-anything-r.md
