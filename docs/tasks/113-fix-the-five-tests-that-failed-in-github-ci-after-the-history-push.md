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
4. Add a dated note to [93] and [94]'s task files: the run above, what it showed,
   and that both finish when `main`'s CI is green on GitHub.

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
