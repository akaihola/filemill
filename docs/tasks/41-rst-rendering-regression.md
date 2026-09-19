---
depends-on: []
---

# Fix plain-text reStructuredText previews in Source and Rendered modes

## Original report and requirements

Bug: Task c37c152d-177e-44f1-a643-9ab96d37b75a failed to implement
reStructuredText rendering. In the preview pane, `.rst` files appear as identical
plain unhighlighted text both in `Source` (`?filemill=highlight`) and `Rendered`
(`filemill=render`) modes. Use red-green TDD and a strong model to investigate and fix
this.
