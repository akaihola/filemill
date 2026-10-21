Steward issue, 2026-10-21 14:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 2 h. Source: the steward's triage of the review queue, `<steward-vault>/notes/2026-10-21-left-to-antti-triage.md`.


Two finished items wait in the review queue for the same reason: the server keyboard helper still starts its own browser lifecycle, and the application-local test roots were never qualified by a parallel whole-suite run. Triage section "Prepare the specific repairs", items "Shared Filemill browser fixtures" and "Independent Filemill test roots" (the unnumbered entries in `TASKS.md`).

## Work

1. Move the server keyboard helper onto the shared browser fixture, removing the duplicate lifecycle. Keep every existing browser assertion.
2. Run the documented parallel test command with the application roots isolated, and declare any dependency it needs.
3. Before claiming the original change is preserved or reversible, find its implementation boundary in the history and name the commits.

## Acceptance

- The documented parallel command passes with fixtures isolated, and no test starts its own browser.
- The commits of the original change and of this one are named in the task file.
- The parallel run is the heaviest command here: if hopeli can't hold it under the memory rule, record the readings and stop instead of lowering the bar. Memory: follow your launch prompt's memory rule, and run one heavy command (test suite, browser, build) at a time.
