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

## Findings, 2026-10-10

Local `main` was 7 commits ahead of `origin/main`, not 51; an earlier push had
landed. The newest `publish` run, 37975040277 on 2026-10-09, failed before
reaching the timeouts: all 91 browser tests died at `BrowserType.launch` with
"Executable doesn't exist at .../chromium_headless_shell-1243/...". The
workflow pip-installed `playwright==1.61.0` and downloaded its browsers, then
ran the suites under `uv run --project server`, whose lock resolves 1.63.0
since `e61aaad`.

The two `test-model.py` timeouts were real and reproduced locally. Both tests
stepped down a six-level chain waiting for `path.length` to grow by one per
step, but the right arrow selects the first row of the column it opens, so the
path grows by two. The ancestor-fold test then read `folded` before the
finder's smooth scroll had moved.

## Changes

- `.github/workflows/publish.yml`: install the browsers with
  `uv run --project server playwright install --with-deps chromium`, so the
  version cannot drift from the lock. `setup-uv` moves before that step.
- `server/tests/test_pytest_config.py`: a guard that keeps a literal Playwright
  pin out of the workflow and requires the locked install command.
- `static/test-model.py`: the two tests wait on `sel.length`, then on the
  layout's target (`folded === path.length - 1`) before reading the fold count,
  and compare the scroll position across the left arrow too.

## Validation

- `uv run --project server pytest static` and `... --dev`: 93 passed, 1 failed
  in each. The failure is `test-ui.py::test_storage`: on this host the whole
  browser process exits with SIGTRAP when a page reads a stored OPFS directory
  handle back from IndexedDB. Reproduced in a bare page, with both the headless
  shell and the full Chromium binary of revision 1243 from the Nix bundle, with
  and without the proxy environment. The 2026-10-01 CI run passed it with
  revision 1228. CI with the stock 1243 download decides whether this is a
  Chromium regression or a host artifact.
- `cd server && uv run pytest --cov=...`: 766 passed, 2 failed while three
  browser suites ran at once; both
  (`test_vertical_navigation_preserves_full_fold_with_equal_widths`,
  `test_delete_key_deletes_selected_files_and_directories_but_not_editors`)
  pass when rerun alone.
- The two fixed tests passed five consecutive reruns in both editions.
- Pre-commit: all hooks pass except mypy, which on this Python 3.14 host cannot
  import `zstandard` (its marker skips 3.14). CI runs 3.12 and its lint job
  passed on the same sources on 2026-10-09.
