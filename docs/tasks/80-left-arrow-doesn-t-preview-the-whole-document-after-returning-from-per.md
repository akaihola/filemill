If I select a heading of a Markdown or reStructuredText file in hierarchical browsing, that section is shown in the preview. If I then hit the left arrow key to return to the whole file again, only the section is still previewed.

Render the whole document in the preview area when returning from hierarchical per-section browsing to selecting the whole file in its folder column using the left arrow key.

## Implementation plan

Add regression tests for left-arrow navigation from nested Markdown headings
and reStructuredText sections. Restore the selected document or parent section
through the shared navigator. Keep ordinary folder navigation unchanged.

## Implementation and validation, 2026-10-11

The shared navigator reselects a document or parent section when left arrow
returns to its column. This clears deeper section selections and restores the
preview and URL. Ordinary folder navigation keeps its existing behavior.

Before the fix, the static Markdown regression timed out while waiting for the
parent section preview. Both server regressions timed out while waiting for
the parent document or section URL. All three passed after the fix. The static
regression also checks nested sections, the full RST source, and right-arrow
reentry into the heading column.

The model checks and all pre-commit hooks pass.

Full static validation, both bundle and `--dev`: 92 passed, 2 failed in each.
The storage test hit the Chromium OPFS/IndexedDB crash documented in [87].
The touch-menu test timed out during the concurrent runs, then passed in
isolation and on unchanged main. Two server layout/link failures also passed
in isolation. The vertical-folding test still fails and is documented in [87].

[87]: 87-make-ci-green-so-pages-publishes.md

Full server validation: 774 passed, 4 failed. The rendered-link and preview
layout tests passed in isolation. The vertical-folding failure reproduced on
unchanged main. The Git bundle test passed after putting the user profile's
binaries first in PATH: the server fixture keeps only the directory containing
`rg`, which must also contain `git`. The agent's bundled `rg` directory does
not contain `git`. No unrelated code was changed. Both server regressions also
pass under Python 3.13.
