---
depends-on: []
---

# Make CI green so GitHub Pages publishes

## Original report and requirements

A session in `~/prg/filemill-screencast` found this on 2026-10-09.

GitHub Pages is enabled for `akaihola/filemill` with GitHub Actions as the
source. <https://akaihola.github.io/filemill/> still returns 404, because no
`publish` run has passed. The `publish` job runs only when `test` passes.

The last three `publish` runs failed (2026-09-18, 2026-09-20, 2026-10-01). The
latest, run 36917506270 at `0ac460c`, failed in "Test the bundle and the shared
sources" with two timeouts:

```
FAILED static/test-model.py::test_preview_left_preserves_ancestor_folds
FAILED static/test-model.py::test_preview_left_expands_parent_when_all_columns_are_folded
  playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 30000ms exceeded.
2 failed, 84 passed
```

Local `main` is 51 commits ahead of `origin/main`. A later commit can already
fix these tests. CI has not run on any of them.

The README screencast ends on the Pages URL as "Try Filemill in your browser".
The screencast is not published until that URL works. The screencast also pins
a Filemill commit that must exist on GitHub.

## Acceptance

- `origin/main` contains the current local `main`.
- The `publish` workflow passes on `origin/main`.
- <https://akaihola.github.io/filemill/> serves the static edition.
