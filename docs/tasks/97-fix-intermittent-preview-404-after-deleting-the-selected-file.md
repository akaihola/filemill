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
