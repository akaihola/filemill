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
