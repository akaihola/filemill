---
depends-on: []
---

# Report the slowest tests in each CI suite

## Evidence, 2026-10-12

[Run 38155597653](https://github.com/akaihola/filemill/actions/runs/38155597653)
spent 7m 6s on the two static suites and 7m 32s on the server suite. Its logs
contain suite totals but no per-test duration report. Browser fixtures start
Playwright, Chromium and server processes repeatedly; measure their contribution
before changing fixture lifetimes or adding pytest workers.

## Requirements

Add `--durations=20` to all three pytest commands in
`.github/workflows/publish.yml`: static bundle, static development, and server
with coverage. Keep their reports distinguishable, whether the suites run in
the existing job or in separate jobs. Preserve the tests, coverage flags and
failure behavior.

Read a completed CI run and record the slowest tests with their setup, call or
teardown phase, plus each suite's total time. Distinguish expected waits from
failed-test timeouts and repeated process startup. Use the findings to propose
specific follow-up work; reuse the existing task for replacing fixed sleeps.

## Acceptance

- All three suite logs show pytest's slowest-duration summary, including test
  identifiers and phases, also when tests fail.
- A dated analysis links the measured run and records the principal delays.
- Browser reuse, additional workers and timeout changes are considered only
  after the measurements; this task adds reporting rather than refactoring
  the test harness.

## Implementation, 2026-10-14

`.github/workflows/publish.yml` runs each suite in its own step with
`--durations=20`: "Test the bundle", "Test the shared sources" and "The
server edition". pytest prints the slowest-durations table after failures
too. `server/tests/test_pytest_config.py` checks that the three pytest
commands carry the flag, that the steps exist, and that the later steps
run after an earlier suite fails.

That last guard was added because of
[run 38534616531](https://github.com/akaihola/filemill/actions/runs/38534616531)
(2026-10-14). The bundle suite passed 116 tests in 231.72s. The development
suite failed `static/test-ui.py::test_copy_refusal_fallback[0]` and passed 115
in 237.12s. The step's failure skipped ripgrep and the whole server suite, so
no server report could have appeared. Those steps now carry
`if: ${{ !cancelled() }}`, and the job still fails when any suite fails.
[90] will move the suites into separate jobs; the flag and step names carry
over.

## Measured run

Pending. The workflow change has to reach GitHub before a run can report
durations, and gogo cannot push. After the push, read the three
`slowest 20 durations` tables from the first completed run and record here:

- each suite's total time and outcome,
- the slowest phases with their test IDs, separated into expected waits,
  failed-test timeouts (about 30s each) and repeated Playwright, Chromium or
  server startup in setup and teardown,
- follow-ups. Fixed sleeps go to the existing `wait_for_timeout` task in
  `TASKS.md`. Browser reuse, more workers and timeout changes are proposed
  only if the data supports them.
