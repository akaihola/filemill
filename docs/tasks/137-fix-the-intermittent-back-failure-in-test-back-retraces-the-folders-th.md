Steward issue, 2026-10-21 01:55. Goal: agentic-leverage (filemill is a tier 1 project in `<steward-vault>/Goals.md`). Estimated 1 h.

[The Back regression] fails intermittently on unchanged `main`. The worker for [save protection] saw it on `main` at `5034567a` and recorded it in its branch's architecture review (A4, "Validation, 2026-10-21", commit `bbfd634d` on `pacer-133-protect-saves-from-truncation-and-stale-overwrites-architecture-0d8a9c10`): a diagnostic run recorded a separate `/notes/deep` history entry, so the second Back landed on `/notes/deep` instead of `/notes`. One isolated rerun passed and a later one failed again.

[The roadmap] says a red suite blocks every merge, with no exceptions. So this failure holds the finished [save protection], and it can hold [local-folder search] and any later code change.

## What to do

1. Reproduce at current `main`: run the test alone 20 times and record how many fail. For a failure, record `history.length` and the URL of each entry the test's clicks push (notes, deep, leaf.md, plain.txt, short.txt).
2. Decide whether the test acts before observable state settles, or the product pushes an extra history entry for `deep` depending on timing. Read the history code changed by `a33cb269` ("folder clicks push history again; only keyboard stepping rewrites") and `3bd91e00`, and cite the lines.
3. Fix the cause. If the product pushes an entry it shouldn't, fix the product and keep the test's expectations. If the test acts too early, wait on the observable condition, never a fixed delay ([the waiting guidance]). Don't weaken assertions, skip the test or add retries.
4. Run the test alone 20 times again, then the full server suite once.

## Constraints and acceptance

- Leave the branches for [local-folder search], [test-delay guidance] and [save protection] alone; the steward resumes those workers after this merges.
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

## Cause and reproduction (2026-10-21)

The unchanged test failed **11 of 20** separate isolated runs on main
`5a15bee0` (runs 1, 2, 5, 10, 12, 13, 15, 17, 18, 19 and 20).
All 11 failures had history length 7 and the extra deep entry; the nine
passes had length 6. The test body and production code were unchanged during
these runs.

This is a product race, not an early test action. The document adapter first
promotes Markdown to a potential directory, then declines a title-only file.
If that read exceeds the navigator's 50 ms grace period, navigation appends a
provisional document column. The history key includes it, so the leaf URL
pushes instead of replacing the folder entry. Closing the declined column
cannot undo that push.

- **History policy:** [The model] at `3bd91e00`, lines 17–32, used the
  focused column as the key (line 23). At `a33cb269`, lines 16–31, it restored
  the open-chain key (line 22) and keyboard stepping replacement (line 29).
  Current lines 17–33 still own that policy. It needs no policy change.
- **Loading race:** [Navigation], lines 75–101, appends the pending column
  after the grace period and removes it after rejection. [The document
  adapter], lines 59–80, changes `dir` to false when no outline exists.
- **Missing guard:** [URL synchronization], lines 35–45 before this fix,
  checked only the root listing and a selected directory. A provisional last
  column has no selected child, so that guard allowed the history write.
- **Fix:** wait to synchronize the URL until every open node is a loaded
  directory, including the interval after an adapter declines a node but
  before navigation removes its column. Keep the loading UI and existing
  Back/Forward assertions. This follows [the history decision].

A failing baseline run on main `5a15bee0` recorded these history writes.
The initial page navigation had length 2; initializing the root pushed `/`
with length 3. URLs below omit the temporary loopback origin.

| Click | Operation | URL | History length |
| --- | --- | --- | --- |
| notes | push | `/notes` | 4 |
| deep | push | `/notes/deep` | 5 |
| leaf.md | push (incorrect) | `/notes/deep/leaf.md?filemill=render` | 6 |
| plain.txt | push | `/notes/plain.txt?filemill=render` | 7 |
| short.txt | replace | `/notes/short.txt?filemill=render` | 7 |

The second Back landed at `/notes/deep`, still with length 7. A passing run
replaced the deep entry with the leaf URL at length 5, pushed plain at length
6, and replaced it with short at length 6. The probe wrapped browser history
methods externally; it changed neither the test's waits nor production code.

The new regression holds the outline response until the provisional column
and active read are observable. After releasing it, it checks that a
confirmed outline pushes once and a declined outline only rewrites. There
are no fixed readiness delays, weakened assertions, skips or retries.

## Validation (2026-10-21)

- **Red:** both controlled-response cases failed on the original production
  code: pending history length was 4 instead of 3.
- **Green:** both controlled-response cases and the unchanged Back regression
  passed together (3 passed). Then the unchanged Back regression passed in
  **20 of 20** separate pytest invocations, without the diagnostic plugin.
- **Full server suite:** 1,180 passed, 7 warnings in 1,536.51 seconds,
  with branch coverage enabled. The run completed within the required
  1,800-second timeout. The memory monitor did not stop a validation command.
- **Repository gate:** all pre-commit checks passed (Python/UI lint and
  formatting, mypy, suppression links and bundle consistency). Shared model
  checks passed with the prescribed Deno 2.6.8.

[The model]: ../../server/src/filemill/ui/core/model/deeplink.js
[Navigation]: ../../server/src/filemill/ui/core/nav.js
[The document adapter]: ../../server/src/filemill/ui/adapters/vfs-doc.js
[URL synchronization]: ../../server/src/filemill/ui/core/deeplink.js
[the history decision]: ../adr/0050-history-pushes-on-entering-a-column-rewrites-otherwise.md
[The Back regression]: ../../server/tests/test_browser_new_ui.py
[The roadmap]: ../ROADMAP.md
[the waiting guidance]: ../../server/CONTRIBUTING.md#wait-for-an-element-never-for-a-duration
[local-folder search]: 120-disable-server-search-in-local-folders-from-docs-question-5.md
[test-delay guidance]: 122-clarify-deliberate-test-delays-from-docs-question-8.md
[save protection]: 133-protect-saves-from-truncation-and-stale-overwrites-architecture-review.md
