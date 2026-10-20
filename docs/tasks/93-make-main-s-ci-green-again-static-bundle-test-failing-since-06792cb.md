---
depends-on: [96]
---

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

## Implementation plan, 2026-10-17

1. Confirm the recorded failure and reproduce the assertion race locally.
2. Wait for the expected fold state before checking the threshold geometry;
   keep the shared layout and its single scroll writer unchanged.
3. Run all three threshold cases 20 consecutive times, then the static bundle
   and development suites and required checks.
4. Merge on main, check CI, and complete the tracker pending user acceptance.
   Report a delivery blocker if the prerequisite history rewrite has not been
   published; do not force-push the rewritten history.

## Cause and validation, 2026-10-17

Navigation updates `focusCol` and `path` before layout necessarily applies the
scroll. In `ui/core/layout.js`, `dialTo(..., true)` can defer its write with
`requestAnimationFrame` when an instant write happened in the same frame.
CSS `scroll-behavior: auto` does not eliminate that deferral. The test now
waits for the expected `folded` value before its existing geometry assertions.
The production layout and its single scroll writer are unchanged.

Red-green evidence:

- Original CI run 38772512085 has the exact `assert 0 == 1` failure.
- The original test passed 20 ordinary local attempts, confirming that ordinary
  repetition alone did not reproduce the failure on this machine.
- Temporarily wrapping animation-frame callbacks to defer them by ten more
  frames reproduced that same assertion locally before the fix.
- With the wait added, all three widths passed in bundle and development mode
  under that same injected delay. The temporary wrapper was then removed.
- The final bundle test passed 20 consecutive invocations, all three widths
  each time, for 60 passes. Command:

  ```bash
  for attempt in {1..20}; do
    uv run --project server pytest static/test-model.py -k preview_threshold -q || exit "$?"
  done
  ```

Ruff lint and format, Deno format and lint, DOM-free model tests and generated
bundle consistency passed. Mypy passed using Python 3.12, matching CI. The
default Python 3.14 environment reports a missing `zstandard` import in mypy;
that dependency is deliberately conditional on Python versions below 3.14.

Additional failures are tracked separately: [97] records the deletion-preview
404 from the latest main CI run 38957407184; [98] records an unchanged server
mobile-landscape test timing out at folder depth 11 during concurrent local
validation. The server suite was stopped after that failure, with 136 passes.

Full static suites passed with the final change:

| Command | Result |
| --- | --- |
| `uv run --project server pytest static --durations=20` | 116 passed in 540.77 s |
| `uv run --project server pytest static --dev --durations=20` | 116 passed in 555.25 s |

Each reported only the existing Docutils `writer_name` deprecation warning.
The [98] server test passed on its isolated rerun in 13.75 s. The complete
server suite was not finished after its unrelated failure.

## Delivery blocker, 2026-10-17

GitHub main still points at `ff7b314383e7e6df2ad3e4a91bceef8cb16bd35b`,
which has the pre-[96] history. Local main contains the rewritten history.
A normal push cannot fast-forward it. Publishing that history rewrite is
reserved for the user by [96]; this task does not force-push it. The next main
CI run cannot validate this fix until the rewritten main is published. Keep
[93] In Progress until that delivery requirement is satisfied.

## Delivery confirmed, 2026-10-19

The rewritten history and the threshold fix are now on GitHub main. The
[94] follow-up repaired the remaining browser failures and published main
`7da2e69`. [Run 39318918168](https://github.com/akaihola/filemill/actions/runs/39318918168)
passed lint, all 157 bundle tests, all 157 development tests, all 939 server
tests and the Pages deployment. The six served assets match the commit.

The three threshold cases were rerun 20 consecutive times on this main,
together with the four geometry cases: 140 passes, including 60 threshold
passes. No gate or assertion was relaxed. [93] is complete and accepted by the
user. [94] records the detailed local and remote validation.

## User acceptance, 2026-10-19

The user explicitly accepted [93] and requested settling its thread. This
acceptance supersedes the earlier instruction to retain In Progress status.
The delivery status above records the blocker observed on 2026-10-17; no new
CI or publication verification was performed as part of this acceptance.

[96]: 96-remove-the-tailnet-hostname-from-all-files-and-from-history.md
[97]: 97-fix-intermittent-preview-404-after-deleting-the-selected-file.md
[98]: 98-investigate-mobile-landscape-wide-folder-navigation-timeout.md
[94]: 94-move-the-ci-workflows-to-action-versions-that-run-on-node-js-24.md
