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
