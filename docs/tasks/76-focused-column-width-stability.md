---
depends-on: []
---

# Keep the focused column width stable during keyboard navigation

## Original report and requirements

Arrow Down to focus the next folder sometimes half-folds the column, dims the
text, and shows a semi-transparent vertical folder name on top of the contents. The
same doesn't happen when navigating by clicking the next folder using the mouse
instead. Ensure navigating up/down using the keyboard never resizes the focused
column, especially not below the folding transition width range.
