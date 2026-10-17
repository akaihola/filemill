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


## Cause and fix, 2026-10-17

The test server could stop answering requests because its access log filled
an unread subprocess pipe. This is a test harness failure. No shared UI change
is required. Linux normally gives these pipes 65,536 bytes on the validation
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
The blocked depth depends on how much startup and request output precedes it. The same test passes with file-backed logs. A separate 4,096-byte
reproduction under Python 3.14.7 blocked during initial page loading.

The unchanged landscape test passed in isolation under Python 3.14.7 in
12.80 seconds and Python 3.12.14 in 12.71 seconds. Both versions use the locked
Playwright 1.63 and Nix Chromium. Python 3.12 came from the installed Nix
interpreter and used a separate uv environment. Its Playwright driver started
without an override. No browser installation or UI change was needed.
