---
depends-on: []
---

# Fold columns and enter fullscreen with preview arrow keys

## Original report and requirements

Pressing the right arrow key when the preview pane is focused currently widens the
pane in small steps. It should instead collapse the leftmost expanded folder column
fully. When all columns are collapsed, it already correctly scrolls them out of view
to the left to fill the window with the preview. One more press must go fullscreen,
similar to pressing the `Fullscreen` button. A left arrow press must exit fullscreen,
equivalent to `Esc`.
