Steward issue, 2026-10-19 21:00. Goal: agentic-leverage; filemill is tier 1.
From question 1 of [[109]](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md)'s
docs check. Labelled `security`.

`SECURITY.md` promises that HTML previews are sandboxed. A file on disk gets an
`<iframe sandbox="">` (`ui/core/renderers.js`), but an `.html` member of an
archive is previewed through `/api/preview?v=` by `_preview_html` in
`server/src/filemill/preview.py`, whose `<iframe>` has no `sandbox` attribute.
Checked on `main` at 21:00 on 2026-10-19: still none. So a crafted archive can
run script in the preview with filemill's origin.

## What to do

1. Write a failing test that previews an archive's `.html` member and asserts
   the iframe is sandboxed (no `allow-scripts`, no `allow-same-origin`), in both
   editions if both render it.
2. Give the server-rendered iframe the same sandbox as the file-on-disk path,
   and check whether any other server-built preview iframe lacks it.
3. Note the fix in `SECURITY.md` only if its wording needs to change.

## Constraints and acceptance

- Security fix: Antti accepts it, not the steward.
- No push, no deploy, no service restart.
- Memory: before each browser or test command, wait up to 10 minutes for
  `MemAvailable` of at least 2 GiB; if it doesn't come, start anyway when at
  least 1.5 GiB is available. Stop a running check, and record it as
  unavailable, when `MemAvailable` falls below 1 GiB or swap grows by more than
  512 MiB.
- The new test fails before the fix and passes after; the server suite passes.
