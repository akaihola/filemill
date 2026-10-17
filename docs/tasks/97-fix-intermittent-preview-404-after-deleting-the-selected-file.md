# Fix intermittent preview 404 after deleting the selected file

Found while validating [93] on 2026-10-17. This is a separate failure from
its static preview-threshold assertion race.

Main CI run 38957407184 failed in
`tests/test_browser_new_ui.py::test_delete_key_deletes_selected_files_and_directories_but_not_editors`.
The deletion assertions passed, but `page.errors` contained an HTTP 404.

Task [91] already recorded this failing about one run in six for
`/api/raw?p=short.txt` after deletion, including with the earlier per-test
fixtures. Task [90] also records the same failure. It still needs a fix.

Reproduce the race, add a failing regression, and fix the preview request or
test synchronization according to the cause. Preserve error checking and
verify repeatedly that deleting the selected file leaves no failed request.

Evidence: https://github.com/akaihola/filemill/actions/runs/38957407184

[93]: 93-make-main-s-ci-green-again-static-bundle-test-failing-since-06792cb.md
[91]: 91-report-the-slowest-tests-in-each-ci-suite.md
[90]: 90-run-the-static-bundle-static-development-and-server-ci-suites-in-paral.md

## Plan, 2026-10-17

1. Pause the preview byte read and the editability byte read in browser tests.
   Delete the selected file or its containing folder while that read is pending.
   Keep console error checks and check failed HTTP responses.
2. Track active preview fills in the shared core. Block new fills for entries
   under a pending deletion. Finish existing fills before calling `FS.remove`.
3. Repeat the regression and the original keyboard test. Run the server and both
   static suites, the model checks, and pre-commit. Record the results here.

This change addresses the deletion race within architecture finding A9. It does
not replace the preview lifecycle or change the filesystem port contract.

## Result and validation, 2026-10-17

Delete could overtake either byte read in `fillPreview`: preview rendering or
editability detection. Generation checks prevented stale DOM writes but did not
keep the file available until these reads finished.

The shared core now tracks active preview fills by root and path. A confirmed
deletion blocks new fills under that path and waits for existing fills before
calling `FS.remove`. This includes a preview inside a folder being removed.
The filesystem port and HTTP error checks stay intact. See
[ADR 0078](../adr/0078-delete-waits-for-active-preview-reads.md).

The regression pauses each byte read before the request. It deletes the selected
file or its containing folder, forces another render during deletion, releases
the read, and checks removal, failed HTTP responses, and console errors.

Validation used Python 3.14.7, Playwright 1.63, and Nix Chromium:

- Red: all four regression cases failed on the old implementation with HTTP 404
  from `/api/raw?p=short.txt` or `/api/raw?p=notes%2Fplain.txt`.
- Green: 20 consecutive runs of the four regressions and the original keyboard
  deletion test passed under concurrent suite load. Total: 100 passes, with no
  failed preview requests or console errors.
- Static bundle: 116 passed in 538.91 seconds.
- Static development: 116 passed in 343.94 seconds on the full rerun. The first
  run had 115 passes and a clipboard fixture setup error from `Clock.pause_at`:
  `Cannot fast-forward to the past`. That case passed alone in 2.06 seconds.
- Server: 849 passed and one failed in 837.78 seconds. The unchanged
  `test_arrow_navigation_keeps_fold_animation_running` timed out waiting for
  `focusCol === 1 && path.length >= 2`. The same test failed at the same wait
  on unchanged main under load, using Python 3.13.14. It passed on the fixed
  branch in an isolated rerun in 4.90 seconds. This separate navigation failure
  remains outside issue 97.
- Model checks, pre-commit formatters, linters, mypy, and bundle checks passed.
  Python 3.14 required a local install of the optional `zstandard` package for
  mypy to resolve its compatibility import. No dependency files changed.

The fix is merged locally into main. Publishing is deferred because main contains
other unpushed commits; pushing main would publish work outside this issue.
