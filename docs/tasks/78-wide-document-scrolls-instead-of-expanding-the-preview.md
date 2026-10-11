---
depends_on: []
---

# [78] Wide document scrolls instead of expanding the preview

If an `.rst` file has wide code blocks, a horizontal scroll gesture on the
trackpad on the preview area scrolls the preview instead of widening the
preview. Scrolling the preview horizontally should only activate after the
preview is as wide as fits on the screen.

## Cause

`#preview .pv-body` and `.pv-rich pre` are `overflow: auto` scroll containers
nested inside `#finder`, the dial. The browser gives a horizontal wheel to the
innermost element that can scroll along that axis, so a wide code block takes
the gesture and the dial never sees it. Over a narrow document the wheel chains
up to `#finder` and turns the dial, which is what the user expects everywhere.

## Plan

- Red: a browser test opens `wide.md` at natural, wheels sideways over the
  preview, and expects the dial to advance while the code block's `scrollLeft`
  stays 0; a second gesture from the end of the dial scrolls the code block.
- Green: `ui/core/layout.js` listens for `wheel` on `#finder` without
  `passive`. A mostly horizontal wheel whose target is inside `#preview` while
  the dial is short of its end is prevented and applied to the finder's own
  scroll instead. The gesture latches: once the dial has taken a wheel, the
  rest of the gesture (until the dial settles) stays on it even after the end
  is reached, as a browser latches a gesture to one scroller.
- ADR 0076 records the decision; `docs/ARCHITECTURE-REVIEW.md` notes it under
  the fold dial.

## Independent-review correction, 2026-10-11

Fullscreen fills the window without moving the dial to its end. The original
wheel interception therefore moved the hidden dial instead of scrolling wide
content, in both native fullscreen and its layout fallback.

The shared layout now checks `pvFullscreen` before the wheel latch and leaves
fullscreen gestures to the preview. Browser regressions cover the first
sideways wheel in both fullscreen modes and entering fullscreen during an
already latched gesture. All three failed before the fix: the dial moved from
0 to 200 in fullscreen, and the latched wheel remained prevented. ADR 0076 and
the architecture review record the exception; the static bundle is rebuilt.

Validation: 19 fullscreen and fold-gesture browser cases pass, plus two static
fullscreen-navigation cases in each build. Model and documentation tests,
formatting, lint, mypy, and the bundle freshness check pass.
