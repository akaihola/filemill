---
depends-on: []
---

# Status bar hints wrap and get clipped

## Original report and requirements

A review session found this on 2026-10-10 at HEAD
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

## Independent-review correction, 2026-10-11

The original whole-strip wrapping also hid long copy feedback, clipboard-refusal
instructions and the fold count. Keep status text in one visible row with
bounded, shrinkable messages. Only keyboard hints may wrap into hidden rows.

Extend the regression test to 838 × 640, 390 × 844 and 568 × 320 px with idle,
long-path copy success, clipboard refusal and long delete feedback. Require all
active status items and the fold count to remain visible, allow only whole hints
to disappear, preserve hint priority and keep the full fallback path selected.
ADR 0074 records the corrected layout. User acceptance remains pending.

Validation: the extended copy test first failed at all three sizes with hidden
copy feedback and fold counts. Long delete feedback also failed at 390 px before
its width was bounded. After the fixes, 5 focused server browser tests, 10 static
bundle tests and 10 static source tests pass. Ruff, formatting, mypy, Deno lint,
model checks and the generated-bundle check pass. These were focused runs, not a
full-suite rerun.
