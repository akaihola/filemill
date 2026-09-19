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

## Related work

Keep this regression separate from the [browser rendering experiment][27] and
[earlier rendering fix][50]. Kandev task `c37c152d-177e-44f1-a643-9ab96d37b75a`
reported merge `5aa3f32` on 2026-09-17, but this later report was added in
`3764d30`. The earlier completion is not evidence that this regression is fixed.

[27]: 27-rst-in-browser.md
[50]: 50-rst-rendering-first-regression.md
