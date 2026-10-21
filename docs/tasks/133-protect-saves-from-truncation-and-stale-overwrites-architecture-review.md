Steward issue, 2026-10-20 22:30. Goal: agentic-leverage (filemill is tier 1). Estimated 2 h.

[The re-checked architecture review](../ARCHITECTURE-REVIEW.md#a4-saves-can-truncate-or-overwrite-newer-content) (filemill [132], 2026-10-20) ranks A4 first in its remediation order and as the only open P1 finding. A failed server write can lose the old file, and nothing stops a save from overwriting newer content.

## Work

1. Server: replace a file atomically (write a temporary file in the same directory, flush, then rename over the target), so a failure at any point leaves the old bytes intact. Enforce the request-size limit while reading the body rather than after buffering all of it, and run the blocking save off the event loop.
2. Carry a revision from read to save on every supported write port (server, browser-owned folders, native). A save whose expected revision no longer matches fails with a conflict, and the UI keeps the user's draft.
3. Browser-owned files (`ui/adapters/fsa.js`): recheck for an external change before writing, and abort the stream explicitly after a failed write.
4. Write down how replacement treats symlinks, hard links, ownership and permissions, in the code's docstrings and the relevant ADR or `SECURITY.md` section, and test each case the server supports.
5. Keep [the editor task][28]'s explicit navigation-discard policy and A3's save and delete authorization as they are.

## Acceptance

- Failing regressions first: a write that fails after truncation would have started, a stale save, an oversized body, and a browser-owned file changed outside Filemill. All pass after the change.
- The review's A4 entry and the architecture document say what changed; mark A4 resolved there only if every acceptance line above holds.
- The repository's own suites pass for the parts you touched. Memory: before each suite, wait up to 10 minutes for `MemAvailable` of at least 2 GiB; start anyway at 1.5 GiB or more; stop a suite and record it as unavailable if `MemAvailable` falls below 1 GiB or swap grows by more than 512 MiB. Run one suite at a time.
- No deploy, push or service restart.

[28]: 28-editor-features.md

## Validation after main's history repair

2026-10-21: rebased onto main after [the history repair]. The first full
server run had 1,191 passes and two failures in
`test_document_history_waits_for_outline`. Its exact request interceptor
missed the save port's new `snapshot=1` query parameter. Updating the
interceptor retained the test's controlled read and all history assertions.
Both outline cases and the Back regression then passed together (3 passed),
and the full server suite passed all 1,193 tests. The full static development
suite passed all 176 tests.

Main subsequently merged the public-mode and preview-security repairs. The
branch was rebased again; validation below records the resulting combined
code. No exception to the suite requirement is used.

[the history repair]: 137-fix-the-intermittent-back-failure-in-test-back-retraces-the-folders-th.md

## Final validation on the combined code

2026-10-21, based on main `af6cd23a`:

- **Server:** 1,248 passed in 1,961.02 seconds.
- **Static development:** 177 passed in 964.76 seconds.
- **Static bundle:** 177 passed in 959.58 seconds.
- **Native:** rebuilt the host; 19 bridge checks passed, followed by both shared
  editor scenarios (2 passed, 70 deselected).
- **Models:** shared model checks passed.
- **Repository gate:** all seven pre-commit hooks passed. An extra blank line
  introduced while resolving the adapter README conflict was formatted before
  the successful rerun.
- **Documentation:** all 27 checks passed after updating the review and ADR.
- **Memory:** one validation suite ran at a time. Each started with at least
  2 GiB available. The monitor enforced the 1 GiB available-memory floor and
  512 MiB swap-growth limit; no final suite was stopped for these limits.

The native build recovered from a cache's HTTP 504 responses using the public
Nix cache. No deployment, push or service restart was performed. The [architecture
review] and [replacement ADR] record the implementation and its remaining external
writer race limit. Task completion awaits user acceptance.

[architecture review]: ../ARCHITECTURE-REVIEW.md#a4-saves-can-truncate-or-overwrite-newer-content
[replacement ADR]: ../adr/0090-revision-checked-file-replacement.md
