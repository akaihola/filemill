---
depends-on: []
---

# Return preview focus to the containing folder and selected file

## Original report and requirements

Bug: Task bf3498e4-4824-4c34-b7f4-25f7efe8fef7 fixed the `ArrowLeft` navigation
out from the preview pane incorrectly. Focus now moves to the parent folder of the
containing folder of the previewed file. Instead, the containing folder column should
be focused with the previewed file highlighted.
