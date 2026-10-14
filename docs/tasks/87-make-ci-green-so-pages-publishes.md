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

## Blocked on the push, 2026-10-10

Local `main` is fast-forwarded to `5ee500f` and contains the fix. Every push
from `agent@gogo` returns 403, for `main` and for a feature branch alike,
inside and outside the sandbox, although the token reports push permission on
the repository. Per the push rules in `~/.config/coding-agents/sandbox.md`,
pushing stops here.

Remaining steps, from `akaihola@atom`:

1. `git push origin main`.
2. Watch the `publish` run. The open question is `test-ui.py::test_storage`
   on the stock Chromium 1243 download (see Validation above).
3. Check <https://akaihola.github.io/filemill/>.

## CI result and the storage fix, 2026-10-11

The user pushed `263288f`. Run 38147875268 found the browsers and ran the
static suite: 97 passed, 1 failed, `test-ui.py::test_storage`, with the same
browser abort as on this host. So it is Chromium 153.0.8010.12 (Playwright
revision 1243), not a host artifact.

Community reports narrow it down: the browser process aborts when an
off-the-record context reads a stored `FileSystemHandle` back from IndexedDB,
while a persistent profile reads it back fine. Playwright's `launch()` +
`new_page()` is off-the-record. Reproduced both halves here in a bare page.
`test_storage` now uses `launch_persistent_context` with pytest's `tmp_path`
as the profile. Passes in both editions, four runs each.

The app's own `recallRoots()` takes the same path, so a user who opens the
static edition in an incognito window of that Chrome would hit the abort.
That is a browser bug outside this task; no app change was made.

## Second CI run, 2026-10-11

Run 38155597653 on `ea20d27`: both static suites passed (98 each, the storage
test included). The server edition failed 10 of 721:

- Five `test_api.py` search tests got 503 "Search is unavailable: ripgrep is
  not installed", and four browser search tests timed out on the same cause.
  The runner image lacks ripgrep. The workflow now installs it before the
  server suite; a guard test keeps that order.
- `test_context_menu_delete_cancel_then_confirm[short.txt]` read the preview
  text empty right after the delete. The preview re-renders after the listing
  refresh, so the test now waits for the text instead of reading it once.

## Third CI run, 2026-10-12

Run 38252850595 on `3d830e7`: search and delete now pass. One failure,
`test_markdown_headings_open_as_columns_in_the_server_build`, reproduced
locally. A bare `/n/<file>` URL parses to the default view, raw, so the shell
carried `data-filemill="raw"`. Since `1c179ef` the view toggle trusts that
attribute instead of the URL, so it read "Rendered" on a rendered section and
clicking it changed nothing. The shell now coerces raw to render, with a route
test for the bare and explicit-raw cases.

The same run skipped all 65 `test_browser_keyboard.py` tests: the suite
skipped itself when `PLAYWRIGHT_BROWSERS_PATH` was unset, a dev-machine
convention CI does not follow. The skip is gone; a missing browser now fails
loudly at launch instead.

## Fourth CI run, 2026-10-14

Run 38534616531 on `3723854`: the bundle suite passed (116) and the modular
suite failed one test, `test_copy_refusal_fallback[0]`, reading the fallback
selection empty. The `copy_page` fixture clicked `note.md` and yielded while
the preview was still loading; the preview's late render rewrites the status
path and drops a selection made before it. The fixture now waits for the
preview. All 30 copy tests pass in both editions. The server edition did not
run in this round.
