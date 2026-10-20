Steward issue, 2026-10-19 20:50. Goal: agentic-leverage; filemill is tier 1.
Follows [[93]](93-make-main-s-ci-green-again-static-bundle-test-failing-since-06792cb.md)
and [[94]](94-move-the-ci-workflows-to-action-versions-that-run-on-node-js-24.md).

[96]'s rewritten history reached GitHub on 2026-10-19 (Antti pushed `a0bfd958`),
so CI ran on `main` for the first time since 10-16:
[run 39292689552](https://github.com/akaihola/filemill/actions/runs/39292689552).
Lint passed. Five tests failed, all of which passed locally when [93] and [94]
finished on 10-17:

- Server suite (1 failed, 938 passed):
  `tests/test_browser_keyboard.py::test_parent_column_survives_preview_after_arrowleft_arrowright_cycle`,
  an assertion on the parent column's URL (it ended in `…/docs` where the test
  expects the root).
- static-bundle and static-development (2 failed each, 151 passed):
  `static/tests/test_ui.py::test_keyboard_horizontal[normal]`
  (`Page.wait_for_function` timed out after 30 s) and
  `static/tests/test_ui.py::test_refresh` (`Page.click` timed out after 30 s).

## What to do

1. Read the failing jobs' logs (`gh run view 39292689552 --log-failed`, with
   `XDG_CACHE_HOME` pointed at a writable directory if `gh` can't write its cache).
2. Reproduce each failure locally. Where the cause is timing on slower runners,
   reproduce under constrained conditions (for example one CPU with `taskset`,
   or Playwright's slow motion) rather than raising timeouts blindly.
3. Fix the cause, in the app or the test, and say which and why. Keep the
   assertions' intent.

## Constraints and acceptance

- No push. The fix reaches GitHub with Antti's next push; say in the completion
  notes that `main` needs one.
- Memory: before each browser or test command, wait up to 10 minutes for
  `MemAvailable` of at least 2 GiB; if it doesn't come, start anyway when at least
  1.5 GiB is available. Stop a running check, and record it as unavailable, when
  `MemAvailable` falls below 1 GiB or swap grows by more than 512 MiB. Run one
  suite at a time.
- The three suites pass locally, including each fixed test 10 times in a row
  under the constrained conditions used in step 2.

Antti accepted [93] and [94] at about 21:08 on 2026-10-19 without waiting for green CI, so this issue doesn't touch them.

## Causes and fixes, 2026-10-20

All five failures were races that CI's faster runner exposed: the test acted
before the page had finished a step. None reproduced on the development
machine as it is, in either static mode, on one CPU (`taskset -c 0`), under
2–6× CDP CPU throttling, with stretched page timers or with reduced motion;
those all slow the test as well. Two causes were reproduced by delaying the
one step the race hinges on, with a throwaway pytest plugin outside the
repository that injects the delay into every page (Blob reads, `/api/`
fetches). [93] reproduced its race the same way. The third, in
`test_refresh`, did not reproduce through that test's own steps; it was
reproduced by staging the dial state that leaves CI's symptom.

### `test_keyboard_horizontal[normal]`, both static modes: the test

← from the preview (`preview-back`) calls `render(true)`, which rebuilds the
preview (A9) and fills it after an asynchronous read. The test then pressed →
and PageDown at once. On a fast runner PageDown arrived before the text, found
nothing to scroll, and the wait for movement timed out. `[deferred]` most likely
passed in CI because its scroll lands three frames later, after the text. [108]'s
"0 → 0" failure on 2026-10-19 was most likely the same race.

- Red: every Blob read delayed by 200 ms failed both variants at line 1442 with
  CI's `Page.wait_for_function` timeout.
- Fix: wait for the leaf's text and a scrollable preview body before the first
  scroll key. The scroll assertions are unchanged. Rebuilding the preview on
  ← stays part of A9.

### `test_refresh`, both static modes: the app

`layout()` re-rests the dial only when its resting place differs from the
current dial. A refresh can end on an instant dial write followed by a glide
to its resting place, the glide queued for the next frame or started but not
yet moved. A mount in that window computed the root's resting place, 0, found
the dial already there and issued nothing. The old glide then landed at 248,
which folds a lone column, and the focused root became a spine. Its rows were
hidden, so `deep_chain()`'s click waited 30 s on an invisible row. That breaks
[ADR 0022]: a resting place never folds the focused column.

- Red: the new `test_mount_stops_a_glide_that_would_fold_the_root[queued]` and
  `[started]` stage that window, dial at 0 with a glide to the fold queued or
  just started, then mount. On the unfixed bundle both ended
  `{"folded": 1, "dial": 248, "cls": "col focus spine"}`.
- Fix (`ui/core/layout.js`): a glide waiting for its frame starts only if no
  later dial write replaced it, and a resting layout that finds a glide
  heading off its resting place stops it with an instant write to the current
  position. Chromium cancels a running smooth scroll on such a write. No ADR:
  this restores ADR 0022's rule rather than changing it.

### `test_parent_column_survives_preview_after_arrowleft_arrowright_cycle`, server: the test

Committing the `docs` folder writes its URL in the render that opens its
column, once the listing lands or after the 50 ms grace. The test read
`page.url` as soon as `sel[1] === 'docs'` held, inside that window. `page.url`
is also updated from the browser's navigation events, which can trail the
test's own `evaluate` round trips. CI captured `/my-knowledge`, and the URL
reached `/my-knowledge/docs` before the final read. The second half has the
same race for `AGENTS.md`: a Markdown file opens after its headings are read,
and `_expect_preview` passed on the previous preview's text.

- Red: `/api/` fetches delayed by 30, 40 or 50 ms failed 9 of 15 runs. Six
  failures had CI's assertion; three failed the same way in the `AGENTS.md`
  half.
- Fix: wait for the render that opens each selection (the `docs` column, the
  `AGENTS.md` preview) and compare `location.href`. The URL-unchanged
  assertions stay.

## Validation, 2026-10-20

Every browser and test command ran behind a memory gate: start at 2 GiB
`MemAvailable`, stop below 1 GiB or on 512 MiB of swap growth. No run was
stopped. Each fixed test, 10 consecutive runs under the condition that
reproduced its failure, stopping at the first failure:

| Test | Condition | Result |
| --- | --- | --- |
| server ←/→ URL cycle | `/api/` fetches +40 ms | 10/10 |
| `test_keyboard_horizontal`, both variants, bundle | Blob reads +200 ms | 10/10 |
| `test_keyboard_horizontal`, both variants, `--dev` | Blob reads +200 ms | 10/10 |
| `test_mount_stops_a_glide_that_would_fold_the_root`, bundle | staged glide | 10/10 |
| `test_mount_stops_a_glide_that_would_fold_the_root`, `--dev` | staged glide | 10/10 |
| `test_refresh`, bundle | one CPU, `taskset -c 0` | 10/10 |

The server test also passed 15/15 at +30, +40 and +50 ms, where the original
failed 9/15.

Full suites, one at a time, with CI's commands:

| Suite | Result |
| --- | --- |
| `uv run --project server pytest static/tests --bundle --durations=20` | 155 passed in 352.29 s |
| `uv run --project server pytest static/tests --dev --durations=20` | 155 passed in 362.26 s |
| `uv run pytest --cov=src/filemill --cov-branch --cov-report=term-missing --durations=20` in `server/` | 971 passed, 1 failed in 581.71 s; coverage 91% |

The one server failure was the documentation portability guard reading a
placeholder file that the sandbox mounts into the checkout (`PermissionError`
on `.claude/loop.md`). Run outside the sandbox, `tests/test_docs.py` passed
20/20.

Ruff check and format, `deno fmt --check ui/`, `deno lint ui/` with Deno
2.6.8, the DOM-free model tests and `static/build-index.py --check` passed.
Mypy was not run: no Python source changed.

The shared `layout.js` also drives the native WebKitGTK shell.
`nix-shell native/shell.nix --run 'uv run --project server pytest
static/tests/test_ui.py --native -k "mount_stops_a_glide or test_refresh or
test_keyboard_horizontal"'` passed 5/5. A first native run showed that
`NativePage.click()` takes no `timeout` argument, so the new test uses the
default; the runs above used a 5 s click timeout, with the same assertions.

Not changed here:

- Under 3× CPU throttling, `test_refresh` once timed out at
  `wait_for_function("path[1]?.loading")`: the 400 ms `racing` read can
  finish before a slowed test first looks. That is the opposite race, a slow
  test, and not one of CI's failures.
- Other checks in `server/tests/test_browser_keyboard.py` still compare
  `page.url` right after keyboard navigation. They passed in CI.

Delivery: nothing was pushed. `main` reaches GitHub, and CI runs on it, with
Antti's next push.

[93]: 93-make-main-s-ci-green-again-static-bundle-test-failing-since-06792cb.md
[108]: 108-wait-for-pagedown-scrolling-in-the-static-keyboard-test.md
[ADR 0022]: ../adr/0022-the-dial-s-resting-place-never-folds-the-focused-column-nor-anything-r.md
