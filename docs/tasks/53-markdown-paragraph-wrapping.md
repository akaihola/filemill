---
depends-on: []
---

# Let Markdown paragraphs wrap to the preview width instead of preserving linefeeds

## Original report and requirements

Bug: Markdown preview doesn't fill and wrap paragraphs at the width of the
preview, but keeps linefeeds. Consecutive lines of text must be considered as a single
paragraph. If this can't be changed by configuring the Markdown renderer currently in
use, consider alternative renderers, check whether they support the other features
currently supported (e.g. checkboxes and wikilinks). Tradeoffs must be discussed with
the maintainer before implementing.

## Related report

Markdown preview now preserves line breaks. It should instead let the browser handle
line breaks and consider a multi-line Markdown paragraph as a single line.

## Consolidation

Both reports describe the same paragraph-wrapping requirement and are retained
here. The completed fix is recorded in `3470ea9` and `effac31`. Portrait overflow
in [54] is a separate layout defect.

[54]: 54-portrait-markdown-width.md
