---
issue: 81
title: Horizontal scrolling fold "stops"
status: in progress
depends_on: []
---

# Horizontal scrolling fold "stops"

## Request

When I swipe quickly on a touchpad right or left, the horizontal scrollbar
correctly goes all the way to the left or right, respectively. Currently on
Filemill these correspond to "all folder columns at full width, preview fills the
rest" and "preview fills the window", respectively.

I want the first swipe to the left to stop at the point where the rightmost column
is fully expanded but all the columns left of it are fully folded. The next swipe
should also fold the rightmost column. The last swipe should fill the window with
the preview and hide the columns.

Swipes to the right should do the same stops in reverse, and additional swipes to
the right should increase column width so one less column fits in the window and
the visible columns fill the window. So e.g. typically the current extreme
scrollbar position at the left after the right swipe shows almost four full
columns. The next swipe should fill the width of the screen with three columns.
The next swipe with two. And if the screen is a narrow portrait screen, yet
another swipe should fill the screen with the leftmost, root column.

The way I envision this would work is to always rely on native scrolling. So the
next swipe stops to the left and right would correspond to the current extreme
ends of the horizontal scrollbar. When a swipe has settled at either far edge, the
page scroll width is "recomputed" so the next stop in that direction becomes the
extreme end of the scrollbar, and the scrollbar position is updated to correspond
to the current stop position relative to the new range.

## Plan (2026-10-11)

### The dial today

`#finder` scrolls horizontally over `#rail`, whose width is the stage plus
`range()` (the natural span of every column). `#stage` is sticky, so nothing
translates; `scrollLeft` is read as a dial ([ADR 0021]): `k × unit` folds the
leftmost `k` columns, `unit = 0.99 × range / n`, 99 % folds all `n`, and the last
percent slides the spines away. Only `ui/core/layout.js` writes the dial;
`advancePreviewFold` (→ in the preview) and `unfoldTo` (spine click) in
`ui/core/nav.js` go through it.

### The dial with stops

One logical axis, `x`, in pixels. `x ≥ 0` keeps today's meaning. `x < 0` is
new: columns widen so that fewer of them fill the finder.

Stops, in order from the right end of the axis to the left:

| stop                   | `x`                          | what shows                                                   |
| ---------------------- | ---------------------------- | ------------------------------------------------------------ |
| preview alone          | `range`                      | spines slid away (today's 100 %)                             |
| all folded             | `0.99 × range` = `n × unit`  | `n` spines, preview fills the rest (today's 99 %)            |
| rightmost column whole | `(n − 1) × unit`             | `n − 1` spines, column `n − 1` at natural width, preview     |
| natural                | `0`                          | every column at natural width, preview off the right edge    |
| `N` columns fill       | `−j × unit`, `j = 1 …`       | the leftmost `N` columns share the finder width, `N = F − j` |

`F = max(1, round((stageW − gutter) / (natural + gutter)))` is how many natural
columns fit the finder, capped at `n`. The widest stop is `N = max(1, F − 1)` and
`N` counts down to 1 on every screen (open question 1). Equal stops are merged,
so a root-only path has `natural`, `all folded`, `preview alone` and `1 column`.

The **scroll range is a window** `[lower, upper]` of two consecutive stops.
`rail.width = stageW + (upper − lower)`, `x = lower + finder.scrollLeft`. At a
stop `s_i` the window is `[s_{i−1}, s_{i+1}]`, clamped at the ends of the axis.
Between stops it is the pair that encloses `x`. A fast swipe therefore clamps at
the next stop in its direction, because that stop is the end of the scrollbar.

**Settling.** The window is recomputed when the dial has been still for
`SETTLE_MS` (≈180 ms) with no `scroll`, `wheel` or `touchmove` event and no
pointer held down on the finder. The recomputation is invisible: `lower` moves
and `scrollLeft` moves by the same amount in one instant `scrollTo`. A held
finger or a scrollbar drag therefore never has its range changed under it.

**Programmatic moves** (`layout`, `advancePreviewFold`, `unfoldTo`) go through
one `dialTo(x, smooth)`: if `x` is outside the window the window first grows to
enclose both the current `x` and the target's own window, then the scroll
glides; settling narrows the window again.

**Widened geometry.** At `x < 0` with `u = −x / unit`, `j = ⌊u⌋`, `t = u − j`,
column `i` is `S_j(i) + t × (S_{j+1}(i) − S_j(i))` where `S_j(i)` is the width
of column `i` at stop `j`: `(stageW − (N_j + 1) × gutter) / N_j` for `i < N_j`,
natural otherwise, and `S_0` is natural everywhere. The focus pan fades out over
the first widening unit; `folded` stays 0; nothing is a spine.

**Resting place after a tap** ([ADR 0022]). Today `automaticFold` picks `k`.
When the dial rests widened and the focused column or the column it just opened
would be outside the `N` visible columns, the dial glides to the nearest stop
that shows them (natural at the latest). Vertical navigation keeps a widened
position the way it keeps a deliberate fold.

**Overscroll.** `#finder` gets `overscroll-behavior-x: contain` so a swipe that
hits a stop does not chain into the browser's back/forward gesture.

### Code

- `ui/core/model/folding.js`: `fitCount`, `fillWidth`, `widenedSizes`,
  `dialStops`, `dialWindow` — pure, tested in `ui/core/model/test.mjs`.
- `ui/core/layout.js`: `base` (the window's lower stop), `dial()`, `dialTo()`,
  `rewindow()`, the settle timer and its holds; `applyScroll` reads `dial()`;
  `applyWidths` uses widened sizes at `x < 0`; `layout()` targets logical `x`.
- `ui/core/nav.js`: `unfoldTo` → `dialTo`.
- `ui/core/debug.js`: expose `dial`, `dialTo`, `foldUnit`, `range`.
- `ui/core/styles.css`: `overscroll-behavior-x: contain` on `#finder`.
- ADR 0075 records the decision; [ADR 0021] is superseded in part.
- `docs/ARCHITECTURE-REVIEW.md` names the stop model.

### Tests (red first)

- Model: stop lists for 1, 3 and 7 columns on 1440 and 390 px; windows at,
  between and at the ends of the stops; widened sizes at and between stops.
- Browser (`server/tests/test_browser_new_ui.py`): a wheel fling from natural
  lands at `n − 1` folded, the next at `n`, the next at preview alone; flings
  right retrace, then fill the finder with `N − 1`, `N − 2`, … 1 columns, the
  preview off-screen; a spine click from fully folded unfolds across windows;
  → in the preview from a widened stop goes to natural first; a tap in a
  widened column that opens a folder shows the new column; a phone viewport
  reaches the root-only stop.
- Existing tests that read `finder.scrollLeft` as the dial read `dial()`
  instead and set it with `dialTo()`; `static/test-ui.py` folds in two swipes.

### Open questions

1. Do the widening stops run down to one column on desktop too, or only on a
   portrait phone? Plan: on every screen.
2. Widened stops show the leftmost columns, so on a deep path the focused column
   can be off-screen until a tap brings it back. Plan: accept, matching the
   natural stop today.

[ADR 0021]: ../adr/0021-horizontal-scroll-fold-dial-not-translation.md
[ADR 0022]: ../adr/0022-the-dial-s-resting-place-never-folds-the-focused-column-nor-anything-r.md
