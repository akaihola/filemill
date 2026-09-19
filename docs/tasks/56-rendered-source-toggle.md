---
depends-on: []
---

# Add a Rendered / highlighted Source toggle beside Raw and Fullscreen

## Original report and requirements

Feature: In addition to the `Raw` and `Fullscreen` buttons, there needs to be a toggle
between viewing the document rendered (e.g. HTML, Markdown, reStructuredText) and
viewing the source with syntax highlighting.

## Related work

The initial toolbar task [63] added the controls (`ff773fc`). This follow-up
implemented rendered versus highlighted previews (`3d505c5`, `68eae0d`).
Task [10] later removed full-page reloads when switching modes. Keep these
separate scopes and completion records.

[63]: 63-preview-toolbar-controls.md
[10]: 10-preview-mode-toggle.md
