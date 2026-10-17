# Investigate mobile landscape wide-folder navigation timeout

Found during [93] validation on 2026-10-17. The unchanged server test
`tests/test_browser_keyboard.py::test_mobile_landscape_wide_folder_tap_keeps_the_touched_row_on_screen`
failed while both static suites and threshold repetition ran concurrently.

`_tap_wide_chain` called `_ui_tap` at depth 11. Playwright timed out after
30000 ms waiting for `.col[data-i="11"]` and its `level-11-` row. The suite
had 136 passes and one failure when stopped to capture this result.

Environment: locked Playwright 1.63, Nix Chromium, Python 3.14.7. The change
for [93] only adds a wait in a static test, so it cannot affect this server
navigation path. Check whether load exposes another navigation race, and
reproduce under CI's Python 3.12 before changing the UI. Keep this separate
from the static preview-threshold fix and the deletion-preview 404 in [97].

Reproduce with:

```bash
cd server
uv run pytest tests/test_browser_keyboard.py::test_mobile_landscape_wide_folder_tap_keeps_the_touched_row_on_screen -q
```

Acceptance: identify the missed navigation state, add or strengthen a failing
regression, and pass repeated runs under load without sleeps or weakened
visibility checks.

[93]: 93-make-main-s-ci-green-again-static-bundle-test-failing-since-06792cb.md
[97]: 97-fix-intermittent-preview-404-after-deleting-the-selected-file.md

## Follow-up validation, 2026-10-17

The same test passed on an isolated rerun in 13.75 seconds using the original
Python 3.14.7 environment. Treat the timeout as intermittent until its cause
is established. A Python 3.12 rerun could not start Playwright's driver in the
temporary environment; it did not exercise navigation.

## Investigation plan, 2026-10-17

1. Run the unchanged landscape test under Python 3.12 and 3.14.
2. Reproduce log backpressure with a small Linux subprocess pipe before
   changing any UI code. The keyboard suite captures server output in an
   unread pipe, whose capacity can shrink under concurrent process load.
3. Keep subprocess diagnostics without blocking requests, then repeat the
   landscape regression with both static suites running concurrently.
4. Run the keyboard suite and repository checks, and record the result here.

## Investigation and fixes, 2026-10-17

The test server could stop answering requests because its access log filled
an unread subprocess pipe. This is a test harness failure. No shared UI change
was made. Linux normally gives these pipes 65,536 bytes on the validation
host. Concurrent suites can exhaust the per-user pipe page allowance, which
reduces new pipes to 8,192 bytes. Long directory URLs fill that space.

The keyboard suite now sends stdout and stderr to a temporary file. Startup
failures still include the captured output. The helper stops the subprocess
before reading that file, so collecting diagnostics cannot wait for pipe EOF.

The added Linux browser regression limits subprocess log pipes to 8,192 bytes
and walks all twelve folders. It failed before the fix under Python 3.12.14
with a 30-second navigation wait timeout. The blocked server was in
`pipe_write`. An instrumented Python 3.12 reproduction stopped at depth 9
with that directory appended but `kids === null`, `loading` still set, and
one spinner. Its 8,192-byte pipe contained 7,972 unread bytes. The next long
access-log write could not fit, so the directory response did not arrive.
The blocked depth depends on how much startup and request output precedes it.
The original report predates `ffc5dbf4`, which replaced the tap helper's
600 ms sleep with a loading predicate. That older helper could continue to
the next row while the preceding directory request was blocked. The current
helper exposes the same blockage at its loading predicate. The same test
passes with file-backed logs. A separate 4,096-byte reproduction under Python 3.14.7 blocked during initial page loading.

The unchanged landscape test passed in isolation under Python 3.14.7 in
12.80 seconds and Python 3.12.14 in 12.71 seconds. Both versions use the locked
Playwright 1.63 and Nix Chromium. Python 3.12 came from the installed Nix
interpreter and used a separate uv environment. Its Playwright driver started
without an override. No browser installation or UI change was needed.

### Mobile input fidelity

The helper also sent mouse clicks on pages configured for touch input. A new
browser regression records `pointerdown.pointerType` and requires `touch`.
It failed under Python 3.12 with `['mouse']`. The helper now uses Playwright's
real touchscreen tap on touch pages, including spine activation. Desktop pages
still use mouse clicks. All loading and geometry assertions remain intact.

### Missed navigation state

A loaded repetition still timed out after the log fix. Instrumentation then
reproduced the failure at the last folder under Python 3.12. Mouse-down hit
the level-11 row in column 11. Mouse-up landed in column 7, and the click
landed outside any row. The path and selection stayed at level 10. All loaded
nodes had children, there was no spinner, the row menu was hidden, and there
were no page errors. This was not a long press or an unfinished folder read.

Playwright's automatic scroll-into-view turns the finder scroll rail, which
Filemill interprets as its fold dial. A pending layout update can then move
the row between mouse-down and mouse-up. A diagnostic probe confirmed this:
the dial changed from 1505 to 1655 pixels before pointer-down. The original
rest-only geometry assertions missed the lost input target.

The mobile helper now sends real touchscreen input. The landscape regression
also requires every pointer-down and pointer-up to name the intended row and
to carry pointer type `touch`. This covers the input contract that the old
mouse-based helper did not exercise. The original loading and geometry
assertions remain unchanged. No shared UI navigation race was established.

A preparation experiment tried scrolling first and disabling automatic
scrolling during activation. It left the final row outside the viewport after
the layout settled. It was discarded. Revealing an offscreen row legitimately
turns the dial, so a frozen dial is not the required invariant. Correct touch
input and paired event targets are the regression contract.


## Validation, 2026-10-17

All browser runs used the locked Playwright 1.63 and Nix Chromium. Python 3.12
checks used the installed 3.12.14 interpreter in a separate uv environment.
The original 3.14.7 environment also passed the corrected three-test selection.

- Final acceptance selection, including the paired touch-target assertion:
  **8 consecutive repetitions, 24 passed**, under Python 3.12. The early
  repetitions overlapped both static UI entry points on the same host. Every
  landscape chain checked all twelve press/release target pairs and retained
  the original final-row visibility checks. No retries hid a failed run.
- Full server suite after the log fix, collected before the new touch test:
  **851 passed**, 90% combined statement/branch coverage, 967.59 seconds.
- Complete keyboard suite with the corrected touch helper: **66 passed,
  1 failed**, 481.04 seconds. The failure was
  `test_arrow_navigation_keeps_fold_animation_running`. Its initial
  ArrowDown/ArrowRight sequence did not reach `focusCol === 1` before the
  animation check. An isolated rerun under load failed at the same predicate.
  This test does not call the tap helper. It remains outside this issue.
- Full static development suite: **116 passed**, 524.95 seconds.
- Full static bundle suite: **114 passed, 2 setup errors**, 493.47 seconds.
  The unchanged copy fixture installed its clock and then tried to pause at
  that same timestamp after time had advanced. Both failed cases passed on
  rerun, 9.25 seconds. No clock-fixture changes were made.
- Extra concurrent static UI runs exercised both the bundle and development
  entry points as load. They hit existing large-directory keystroke budgets.
  The last pair measured 180.1 ms and 130.7 ms after a size sort. No performance
  thresholds were changed. These stress failures are separate from the
  navigation acceptance checks.
- All pre-commit hooks passed: ruff, ruff format, mypy, Deno format/lint and
  the committed-bundle check. The DOM-free model checks also passed.

No browser sleeps, forced clicks or relaxed visibility assertions were added.
The static preview-threshold fix [93] and deletion-preview fix [97] were not
changed. No application code or deployment assets changed.
