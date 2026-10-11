---
issue: 81
title: Horizontal scrolling fold "stops"
status: completed
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

`F = ⌊(stageW − preview − gutter) / (natural + gutter)⌋`, at least 1, is how
many natural columns fit beside the preview reserve: 3 on a 1440 px laptop
("almost four"), 1 on a portrait phone. The widest stop shows `min(n, F)`
columns and `N` counts down to two, or to one where fewer than two fit (a
portrait phone; decided 2026-10-11). Equal stops are merged. A root alone on a
desktop has no widening stop; on a phone it fills the finder.

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
glides; settling narrows the window again. → in the preview steps one stop per
press, widened stops included. A glide takes no explicit behaviour, so the
stylesheet decides (smooth unless reduced motion), and a glide issued in the
same frame as an instant scroll write waits one frame, because the write would
cut it (seen in mobile emulation). The rail is `calc(100% + range)` so a resize
never clamps `scrollLeft` under the dial.

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

### Decisions (2026-10-11)

1. Widening stops run down to two columns on a desktop and to one only on a
   portrait phone.
2. Widened stops show the leftmost columns; on a deep path the focused column
   can be off-screen until a tap brings it back, as at the natural stop.
3. A swipe has settled after about 180 ms with no scroll, wheel or touchmove
   event and no mouse button or finger held on the finder.

### Validation (2026-10-11)

Model tests pass. The keyboard browser suite passes in full. The new-UI
suite passes except `test_context_menu_delete_cancel_then_confirm[short.txt]`,
which fails the same way on `main` at `20acff4`. The static suites pass except
`test_storage`, a known local red (Chromium 1243 and OPFS handles).

### Independent-review corrections (2026-10-11)

Thread `41779270-752f-45ba-8f46-850db94b0549` received two P2 findings:

- At 1500 → 1000 px, the widening counts change from `[3, 2]` to `[2]`
  without changing column width or path length. The two-column position must
  move from `-495` to `-247.5`; otherwise rebasing leaves a 1 px scroll range.
- At 414 px, rounding the base separately from the rail span leaves the first
  native endpoint at 429 instead of the 429.66 stop. The next fling only moves
  to 430, requiring four flings to reach the preview instead of three.

Layout now detects changes to the widening counts, preserves the column count
at a whole widened stop where possible, and clamps partial positions to the
available range. The rail span is rounded from the adjusted base to the upper
stop. Regression tests first reproduced both findings, including expanding
resizes, partial widening, reverse flings and fractional desktop column widths.
Acceptance remains pending in `TASKS.md`.

Validation: all seven new regression cases pass. The full server run had
807 passes and one Git bundle browsing timeout: the test server's PATH kept
the bundled `rg` directory but omitted `git`. That test passes with the system
tools first on PATH. Both static suites, bundle and `--dev`, pass all 98 tests.
Model tests, formatting, lint, type checks and bundle consistency pass.

[ADR 0021]: ../adr/0021-horizontal-scroll-fold-dial-not-translation.md
[ADR 0022]: ../adr/0022-the-dial-s-resting-place-never-folds-the-focused-column-nor-anything-r.md
