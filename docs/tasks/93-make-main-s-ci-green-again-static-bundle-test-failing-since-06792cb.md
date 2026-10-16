# Make main's CI green again

The first `main` run after merging [90] (`06792cb`), run 38772512085, failed in the
static bundle suite at
`test_preview_threshold_folds_only_below_one_third[1154-1]`, so publishing was
skipped. Main has not published since 2026-10-15. The PR run 38771009899 passed
the same suites (116/116/843 tests), which suggests a timing-dependent test.

- Reproduce the failure locally or from the run log (`gh run view 38772512085 --log-failed`).
- Fix the cause. If the test is timing-dependent, make it wait for the state it
  asserts instead of sleeping or relying on speed.
- Acceptance: the fix is on `main` with the reason in the commit message, the test
  passes 20 times in a row locally, and the next `main` CI run is green or its
  remaining failures are filed as separate issues.

Found by the steward's review of [90] on 2026-10-16.
