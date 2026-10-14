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

## Measured run, 2026-10-14

[Run 38564017994](https://github.com/akaihola/filemill/actions/runs/38564017994)
at 9c67d66 passed every suite. It is the first run with duration tables.

| Step                    | Outcome    | pytest total | Step wall time |
| ----------------------- | ---------- | ------------ | -------------- |
| Test the bundle         | 116 passed | 239.95s      | 4m 1s          |
| Test the shared sources | 116 passed | 241.81s      | 4m 2s          |
| The server edition      | 841 passed | 676.34s      | 11m 18s        |

Server coverage was 90 % of branches and lines combined.

### Static suites

The two editions show the same profile:

- `static/test-ui.py::test_ui` call: 110.01s (bundle) and 109.93s
  (development), 46 % of each suite. This one test runs the scripted UI
  checks in a single browser session.
- `static/test-url.py::test_url` call, 9.28s and 9.44s, and
  `static/test-rich.py::test_rich` call, 8.87s and 10.37s.
- `test-ui.py::test_storage` takes 3.1s. Every other test call is 2.2s or
  less.
- Setup phases are the remaining entries, at 0.75s to 0.81s each. They come
  from `test-ui.py` copy tests and `test-preview-views.py` `browser_preview`
  tests, each of which starts its own browser. The table stops at the top 20,
  so it does not show the total cost of these setups across 116 tests.

The top 20 add up to about 152s of 240s per suite. No test failed, so no
failed-test timeout appears.

### Server suite

- The slowest calls are fold-dial tests, all expected waits.
  `test_fractional_fold_stops_are_native_scrollbar_endpoints` takes 12.34s at
  `[1500-20.025em]`, and 10.04s each at `[414-None]` and `[413-None]`. One
  test makes about 20 flings, and every fling polls `_dial_settled` until
  the dial holds still for three samples. `test_flings_stop_at_each_fold_stop`
  takes 5.98s.
- `test_mobile_landscape_wide_folder_tap_keeps_the_touched_row_on_screen`
  takes 10.04s, and its portrait counterpart 5.64s. They tap a chain of
  folders one at a time and wait after each tap.
- Three different tests stop at exactly 10.04s. That may come from a shared
  ceiling, which passing assertions would hide; it is worth checking.
- The rest of the top 20 are `test_browser_keyboard.py` tests at 2.9s to
  4.4s. `_ui_page` launches a new Chromium for each of them.
- The top 20 add up to about 100s, so about 576s is spread over the other
  821 tests. No setup or teardown phase reaches the top 20. The time is
  spread thinly, which makes a per-test cost such as browser startup or a
  fixed sleep more likely than a few outliers.

### Proposed follow-ups

1. [90] (parallel jobs) would bring wall time to about the server step,
   roughly 11.5 minutes, so the server suite is the critical path.
2. Replace the fixed sleeps through the existing `[*]` task to replace
   `wait_for_timeout` in TASKS.md. It counts 288 calls: 181 in
   `static/test-ui.py`, 40 in `server/tests/test_browser_new_ui.py` and 32 in
   `server/tests/test_browser_keyboard.py`. `test_ui` and the fold-dial
   polling are the first places to measure.
3. Before reusing browsers or adding pytest workers to the server suite, run
   it once with `--durations=0` and add up the setup, call and teardown
   columns. That shows whether the per-test Chromium launch in `_ui_page`,
   and `chromium.launch` elsewhere (16 calls in the two browser modules),
   accounts for the 576s tail.
4. Find out why three tests last exactly 10.04s before changing any
   timeout.
