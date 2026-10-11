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

## Review correction plan, 2026-10-11

R1 found that `autoPreview()` treats headings named `README`, `README.*`, or
`index.html` as folder preview files. After left arrow reselects a document or
parent section, this convention selects a child heading again.

Add failing model and browser regressions for all three names in Markdown and
RST, covering whole-document and parent-section returns. Exclude documents and
sections from automatic folder preview selection. Keep ordinary folder behavior,
regenerate the static bundle, and validate both static builds and server renderers.

## Review correction validation, 2026-10-11

The new model regression failed before the fix: a document automatically selected
its `README` heading. Browser regressions also failed for whole-document and
parent-section returns. `autoPreview()` now excludes document and section nodes.
Ordinary folders still select README and index files automatically.

The model suite and all pre-commit hooks pass. The targeted bundle/server run
passed all 30 tests, including the 24 new Markdown/RST special-heading cases
and existing section, keyboard, ancestor-unfolding, and preview-focus regressions.
The full suites from the original implementation were not rerun for this
one-line model correction.

The development static build passed all 17 document tests. Together with the
bundle/server run, all 47 targeted browser tests pass.

The correction is rebased onto main. The model and bundle checks pass after
rebasing. Merge is blocked by unrelated uncommitted changes in main's TASKS.md,
architecture review, server browser tests, and generated static bundle. Those
changes were preserved. Keep this issue in progress until integration completes;
user acceptance remains pending.

## Integration validation, 2026-10-11

Rebased the review correction onto current main. The model checks, generated
bundle check, and all pre-commit hooks pass. The targeted bundle/server run
passed 29 tests and failed the existing Markdown section Source-mode check.
That failure reproduced in isolation on unchanged main, before this correction
was merged. The development document suite passed all 17 tests. All 36 new
special-heading browser cases pass; the Source-mode failure is independent
of automatic heading selection.
