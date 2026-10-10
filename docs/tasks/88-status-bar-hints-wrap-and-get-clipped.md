---
depends-on: []
---

# Status bar hints wrap and get clipped

## Original report and requirements

A session in `~/prg/filemill-screencast` found this on 2026-10-10 at HEAD
`7ff1fd2`, in an 838 px wide landscape viewport, the README screencast's size.

`#status` (`ui/core/styles.css:1291`) is a 24 px high flex row with
`overflow: hidden`. When its items do not fit, they shrink and their text wraps:
"4/5 folded" in `#st-fold`, and the label after each `<kbd>` in `.status-hints`
and `.status-fold` (`ui/core/shell.js:77-85`), break onto a second line that the
24 px height cuts off. Only portrait phones hide the hints
(`ui/core/styles.css:1308`).

The README screencast shows the status bar in every frame. Fix this before the
screencast is captured.

## Acceptance

- No status bar item wraps at any viewport width.
- When the hints do not all fit, whole hints are hidden, lowest priority first,
  instead of being squeezed or clipped.
- A browser test at 838 × 640 px with columns folded checks that every status
  bar item is one line high.
