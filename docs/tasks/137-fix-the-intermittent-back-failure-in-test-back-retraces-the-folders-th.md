Steward issue, 2026-10-21 01:55. Goal: agentic-leverage (filemill is a tier 1 project in `<steward-vault>/Goals.md`). Estimated 1 h.

`server/tests/test_browser_new_ui.py::test_back_retraces_the_folders_that_were_opened` fails intermittently on unchanged `main`. [133]'s worker saw it on `main` at `5034567a` and recorded it in its branch's architecture review (A4, "Validation, 2026-10-21", commit `bbfd634d` on `pacer-133-protect-saves-from-truncation-and-stale-overwrites-architecture-0d8a9c10`): a diagnostic run recorded a separate `/notes/deep` history entry, so the second Back landed on `/notes/deep` instead of `/notes`. One isolated rerun passed and a later one failed again.

[The roadmap](../ROADMAP.md) says a red suite blocks every merge, with no exceptions. So this failure holds [133]'s finished save protection, and it can hold [120] and any later code change.

## What to do

1. Reproduce at current `main`: run the test alone 20 times and record how many fail. For a failure, record `history.length` and the URL of each entry the test's clicks push (notes, deep, leaf.md, plain.txt, short.txt).
2. Decide whether the test acts before observable state settles, or the product pushes an extra history entry for `deep` depending on timing. Read the history code changed by `a33cb269` ("folder clicks push history again; only keyboard stepping rewrites") and `3bd91e00`, and cite the lines.
3. Fix the cause. If the product pushes an entry it shouldn't, fix the product and keep the test's expectations. If the test acts too early, wait on the observable condition, never a fixed delay (`server/CONTRIBUTING.md`). Don't weaken assertions, skip the test or add retries.
4. Run the test alone 20 times again, then the full server suite once.

## Constraints and acceptance

- Leave the branches of [120], [122] and [133] alone; the steward resumes those workers after this merges.
- Memory: before each command, wait up to 10 minutes for `MemAvailable` of at least 2 GiB; if it doesn't come, start the command anyway when at least 1.5 GiB is available. Stop a running command when `MemAvailable` falls below 1 GiB or swap grows by more than 512 MiB. Run one heavy command at a time, and bound any background job you start.
- Acceptance: 20 of 20 isolated runs pass, the full server suite is green, and the issue file and commit message name the cause.

## Implementation plan (2026-10-21)

- Run the unchanged test in 20 separate pytest processes on current main,
  recording push/replace URLs and history length with an external probe.
- Trace the open-chain history key and asynchronous document loading; capture
  a deterministic failing regression before changing production behavior.
- Fix the cause within the shared navigation boundary, retaining all Back and
  Forward expectations. Regenerate the static bundle if shared code changes.
- Repeat the isolated test 20 times, run the complete server suite and the
  required lint/model/bundle checks, then merge and complete pending acceptance.

All commands use a memory gate and monitor: start at 2 GiB available (or
1.5 GiB after ten minutes), terminate below 1 GiB or on swap growth over
512 MiB. Only one heavy command runs at a time.
