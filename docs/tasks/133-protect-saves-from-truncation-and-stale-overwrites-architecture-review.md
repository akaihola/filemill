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
