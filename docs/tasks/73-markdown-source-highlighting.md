---
depends-on: []
---

# Fix Markdown source highlighting and clickable links

## Original report and requirements

`<file>.md?filemill=highlight` doesn't highlight Markdown files correctly.
Headings and URLs are not highlighted, apostrophes cause highlighting of everything
between them, even if they're just part of a word. Links are not highlighted. Also,
I'd like Markdown links to actually act as clickable links just like in the rendered
Markdown preview.
