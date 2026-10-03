---
depends-on: []
---

# Show copied paths and cycle clipboard formats

## Original report and requirements

When the relative path of a file or folder is copied successfully using `Ctrl+C`
or a context menu item, show the copied path in the status bar, truncated if
necessary. Pressing `Ctrl+C` again within 5 seconds and before any other interaction
must copy the full path, and a third press must copy the item's name only. A fourth
press must start the rotation over from the relative path.
