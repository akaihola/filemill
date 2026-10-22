Steward issue, 2026-10-22 10:45 refill (steward decisions D7 and D95). Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 2.5 h. Unlabelled.

## Why

58 finished filemill items wait in the review queue, the most of any repository. The steward's evidence pass of 2026-10-22 (`<steward-vault>/log/2026-10-22-afternoon-evidence.md`, section "Filemill full suite") could not verify eight of them ([120], [130], [148]–[153]): the documented root command `timeout 1800 uv run pytest` (1,492 tests) was stopped by its bound at 96 %, after one failure marker and with no final summary. The same pass found more red:

- `static/tests/test_ui.py::test_edit_mode` failed in a rerun of the 32 unreported cases (Edit button absent).
- The native UI suite gave 74 passed and five failures: clock and label driver APIs, a native path assertion, render timing, and a delayed-outline selector.
- `server/tests/test_browser_new_ui.py::test_an_offline_copy_of_a_document_is_read_only` is the likely failure marker inside the suite (inferred from collection order) and passed alone.

Older held items fail the same way ("Fix all remaining red tests", [12]). Until one documented command finishes green on this host, no filemill item can be accepted on evidence.

[144] already made the separate static development and bundle suites (185 tests each) pass three times in a row, in 11 to 21 minutes each; read its findings first and don't redo them. This issue is about the root command and the failures above.

## What to do

1. On a clean checkout of `main`, run `timeout 1800 uv run pytest -p no:cacheprovider --junitxml="$TMPDIR/root.xml" --durations=40 -q -rs`. The JUnit file keeps the results if the bound stops the run. Record the wall time, every failure and the 40 slowest tests in this file.
2. Fix each failure at its cause, in the code or the test. Reproduce `test_edit_mode` and the native UI failures. For the offline-copy case, run it after its predecessors in collection order, find the state it inherits, and isolate it.
3. Bring the root run under the bound with margin, aiming at 25 minutes here, by removing waste in the slowest tests: fixed sleeps, repeated browser or server start-ups, duplicated setup. Prefer shared fixtures. If the suite still can't fit, split it in [the test commands](../../CONTRIBUTING.md#tests) into named shards, each under 25 minutes, whose collected test IDs together equal the root collection exactly (compare `--collect-only -q` output), and say there that evidence runs take them one at a time.
4. Keep the native suite's commands as its guide documents them. Fix its five failures, or state for each, with the failing assertion, why it needs hardware or a display this host lacks.

## Constraints

- Preserve every assertion. Getting to green by skipping, marking xfail, deselecting, retrying or loosening a timeout doesn't count. Leave the 1,800-second bound as it is.
- No new dependency unless it removes more than it adds; say why here.
- Memory: follow your launch prompt's memory rule. Run one heavy command (suite, browser, build) at a time, and no parallel whole-suite run: that is [141], which stopped on swap growth.
- Don't restart the filemill services.
- [141] owns the server keyboard helper's browser lifecycle and the parallel-run qualification. Leave both alone unless a failure here needs the same fix; then say so in both task files.

## Acceptance

- On the merged `main`, the root command (or each documented shard, one at a time) exits 0 with a final pytest summary inside its bound on this host, and `timeout 1800 uv run pytest static/tests --dev` passes too. Wall times before and after are recorded here.
- `test_edit_mode`, the offline-copy case and the five native UI cases pass, or each remaining native case has its stated hardware cause and failing assertion.
- The commits are named here. Handoff: a short outcome; details stay in this file.

Tracker: [filemill's tracker](../../TASKS.md).

[12]: 12-test-ui-runs-to-end.md
[144]: 144-make-the-full-static-suites-pass-reliably-the-wide-folder-wait-and-tes.md
[120]: 120-disable-server-search-in-local-folders-from-docs-question-5.md
[130]: 130-give-served-and-browser-owned-folders-the-same-content-search.md
[141]: 141-finish-browser-fixture-isolation-and-qualify-independent-test-roots.md
