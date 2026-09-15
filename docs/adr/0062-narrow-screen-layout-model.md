# ADR 0062: The narrow-screen layout model: what folds, what pans, what stays

Date: 2026-09-15

## Context

ADRs 0021 to 0028 each record one rule of the column strip on a narrow screen.
This ADR collects them in one place. The code of record is `layout()`,
`applyScroll()` and `panFocus()` in `ui/core/layout.js`, the width clamp in
`ui/core/render.js`, and `previewTarget()` in `ui/core/state.js`.

## Decision

- **What folds.** Only columns left of the focused column fold, and only the
  fewest that let the strip plus `previewTarget()` fit `#finder`. A scroll, a
  spine click and `?layout=compressed-columns` may fold every column.
- **What pans.** When the focused column would still overflow, `#strip` slides
  left by exactly the overflow and never past the focused column's left edge.
  `#stage` never scrolls.
- **What stays.** The focused column and its selected row are whole. The
  column a tap just opened starts inside `#finder` when no pan was needed;
  when the pan engages, the focused column wins and the opened column waits
  past the right edge. No column is wider than two thirds of `#finder`.
- **The preview.** Its target width is `previewTarget()`. It grows when the
  strip fits, keeps its left edge on screen when the strip does not, and
  `.pv-fullscreen` hides the columns.

## Measurement

`static/test-ui.py` walks four folders at the 380 px ceiling on 390 x 844,
844 x 390, 1024 x 768 and 1440 x 900. Three ancestors fold on each. At 390 px
the columns clamp to 260 px and the strip pans 11 px, so the opened column
starts off screen. At 844 px and wider nothing pans and the opened column
peeks. On every viewport the checks assert the same promises.

## Consequences

Each promise above has one check per device class. A change to the fold
count, the pan, the clamp or the preview target must update this ADR.
