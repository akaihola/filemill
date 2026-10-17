# Rebase [25]'s pytest migration onto main and merge it once the full suite passes

Steward issue, 2026-10-17. [25] moved the static browser checks under pytest
(`b8e8c588`, branch `pacer-520cb8de-47c1-4a59-a752-1890416fccbb`), but the
red-suite rule kept it from merging: two server tests failed on main as well
(recorded in the branch's copy of [25]'s description). [25] has stayed In
Progress since 08:27 UTC, and the pacer will not launch it again.

Main has moved on since. [97] fixed the delete-key 404, [98] fixed the keyboard
suite's log backpressure and touch input, and `ffc5dbf4` removed all 288 fixed
waits, partly in the files [25] moves. [98]'s validation still saw two
load-sensitive failures on main:

- `test_arrow_navigation_keeps_fold_animation_running` (keyboard suite) did not
  reach `focusCol === 1`, also on an isolated rerun under load;
- the static bundle suite's copy fixture had two setup errors: it installed its
  clock and then paused at the same timestamp after time had advanced.

## Work

1. Rebase `b8e8c588` onto current main in a new worktree. Keep `ffc5dbf4`'s
   removal of fixed waits in the moved tests; its regression guard must pass.
2. Run the full suites: root `uv run pytest`, both static modes, and pre-commit.
3. Fix whatever still fails on main, including the two failures above if they
   recur, without sleeps, forced clicks or relaxed assertions. A failure that
   needs a design decision gets its own issue with a reproduction instead.
4. Merge, then move both [25] and this issue to `## Completed / Accepted` with
   `[ ]`. Leave [25]'s old worktree and branch in place.

## Acceptance

- [25]'s acceptance criteria hold on main.
- The full server suite and both static suites pass on main twice in a row;
  record the timings here.
- `grep -r wait_for_timeout static server/tests` finds nothing.

## Rebase and regression work, 2026-10-17

- Rebased a new copy of `b8e8c588` onto main. The original [25] branch and
  worktree remain unchanged. Preserved the condition waits from `ffc5dbf4`
  and the later JSON depth-limit check in the moved tests.
- Changed the fixed-wait guard to scan the static test directory recursively.
  Confirmed that it failed on waits in the moved tests, then passed after
  their replacements.
- Reproduced the keyboard setup failure with 200 ms of network latency:
  the original animation test failed in 36.45 s. Waiting for the opened
  directory before stepping into it passed in 7.62 s with the same latency.
  The animation assertion is unchanged.
- Reproduced the copy clock setup error under concurrent browser load.
  `pause_at` now installs and pauses the clock in one operation. A remount
  check opens a folded spine before clicking a row. The 15 focused copy
  checks passed in 40.59 s, including the timeout boundary checks.
- The archive cache test now changes the fixture timestamp explicitly.
  Two immediate tar writes can have the same size and timestamp. The
  original assertion failed in the root suite; the corrected fixture passes.
- Reproduced the Back/Forward test failure with 200 ms of network latency.
  Two setup clicks could create an extra intermediate folder history entry.
  Opening the preview directly creates the one entry this test requires.
  Its unchanged assertions passed with the same latency in 8.77 s.
- The first-touch check waits for the dial to settle before pressing a row.
  Its hover visibility, first-tap and long-press assertions remain unchanged.
- Development mode: 147 passed in 544.42 s. Model checks and all six
  pre-commit hooks passed at this checkpoint under Python 3.13.
  The final results below supersede this checkpoint.

## Completion and main validation, 2026-10-17

Merged as `adb7aef3`. Both runs below used that main tree with Python 3.14.
Each suite ran twice consecutively. The three suites ran in parallel.

| Suite | Tests per run | First run | Second run |
| --- | ---: | ---: | ---: |
| server | 853 | 806.51 s | 548.89 s |
| bundle | 147 | 463.40 s | 490.01 s |
| dev | 147 | 494.70 s | 506.02 s |

Commands:

```bash
uv run pytest server/tests -q --tb=short --durations=10
uv run pytest static/tests --bundle -q --tb=short --durations=10
uv run pytest static/tests --dev -q --tb=short --durations=10
```

Before the merge, root `uv run pytest -xq --tb=short --durations=20` passed
all 1,000 tests in 815.02 s. Development mode passed all 147 tests in 544.42 s.

All six `uvx pre-commit run --all-files` hooks pass on main with Python 3.14.
The development groups include the existing locked `zstandard` package so
mypy can check its compatibility imports on Python 3.14. No existing package
version changed. The model checks and recursive fixed-wait guard pass.
`grep -r wait_for_timeout static server/tests` returns 1 with no matches.

The portability guard also found two private paths in the new [100]
description. Only those references and its tracker update time changed.
All 12 documentation checks then passed.

[25] and [99] are completed pending user acceptance. Their checkboxes remain
unchecked. [25]'s original worktree and branch remain at `b8e8c588`.
The temporary rebase worktree and branch were removed after the merge.
