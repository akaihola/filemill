---
depends-on: []
---

# Use stable column widths and responsive preview ratios

## Original report and requirements

Many of the unintended column width changes could probably be solved by using a
constant column width. Choose a standard folder column width in `em` units such that
on a normal laptop widescreen, one column wills 1/6 of a full screen width browser
window. The preview pane should fill the remaining width. The leftmost column should
fold when that remaining width falls below 1/3 of the full screen width. On small
screens such as phone screens, the ratios should be different: for portrait mode,
column = 1/2 width, preview = at least 1/3 width, and for landscape mode, column = 1/4
width, preview = at least 1/3 width. We need to experiment with these.
