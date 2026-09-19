---
depends-on: []
---

# Keep column widths stable during Up/Down navigation

## Original report and requirements

Moving up and down in a folder column using the arrow keys still often causes the
subfolder column to the right to change its width. A bit more seldom but regularly
does the folded width of the parent column change. Let's still aim for complete
stability like described in task 3cf8ab6d-f2b0-4438-bfe1-58870f487bec.

## Related work

[48] covers ancestor folding state. This follow-up also reports changes to the
right-hand subfolder width and the folded parent width, so it remains separate.

[48]: 48-preserve-ancestor-fold-state.md
