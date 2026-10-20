# Remove the obsolete /w/ and /n/ URL routes

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md?f), question 2 and question 7.
User review, 2026-10-20. Label: `steward`.

## Decision

Approved: stop supporting the /w/ named mounts and /n/ alternate shell. Backward compatibility and old links are not required. Paths starting with w or n must instead identify real files and folders normally.

## Work

1. Start with failing route tests for real w and n folders, including their files, and for old alias requests with no corresponding real file. Delete the aliases rather than redirecting them or permanently denying those path prefixes.

2. Remove alias-only routing, mount helpers and URL construction; update UI and browser fixtures to root-relative file addresses. Preserve safe direct-root symlink bookmarks and path containment.

3. Record the new decision in an ADR and update current guidance. Date the change from the historical [task 35 decision](35-decide-web-mounts.md?f) instead of treating that completed decision as an unimplemented instruction. Coordinate the collision matrix with question 6.

## Acceptance

Both former prefixes work as real paths. No special alias handler or compatibility redirect remains. Resource, virtual-file, PWA and affected browser tests pass; the static bundle and architecture description match the new behavior.

## Implementation, 2026-10-20

- Added route regressions first: six failed and two passed before removal.
- Deleted `web_static`, `ui_view`, `UI_BASE`, `mount_targets` and
  `resolve_web_mount`. The server router now always uses `/`.
- Migrated API, resource, PWA, public-mode and browser fixtures to real paths.
  Kept containment and direct-root bookmark checks. Added browser navigation
  and fresh-load coverage for real `w` and `n` folders.
- Browser validation exposed two remaining alias assumptions: the local-folder
  test expected `/n`, and a whole JSON column dropped its render query. Fixed
  the assertion and added a failing model check before preserving that query.
- Recorded ADR 0088, the task 35 replacement date and the collision boundary
  with [121]. Updated current guidance and rebuilt the static bundle.

## Validation

- Red route checks: six failed and two passed before removal.
- Resource, API, containment, PWA and public-mode checks: 519 passed.
- Non-browser server suite: 815 passed, one subprocess timeout after its inner
  check passed. That check passed on retry (1 passed).
- Server browser suites: 306 passed, three failed. The local-folder assertion
  and JSON whole-file URL were corrected. Their focused checks passed
  (1 local-folder case and 3 scalar cases). The Firefox missing-fragment check
  passed unchanged on retry (1 passed). Both new real-prefix browser cases passed.
- Static suites: 159 passed and one failed in each mode. Bundle render cost
  exceeded its 100 ms budget (111.8 ms); development refresh timed out. Both
  passed unchanged on sequential retries (1 passed each).
- After the model change: static URL checks passed in both modes (8 each),
  as did JSON/JSONL UI checks (2 each).
- Model checks and all seven pre-commit hooks passed, including type checks,
  formatters, linters, suppression links and the rebuilt static bundle check.

No thresholds or timeouts were relaxed. The worktree and branch are retained.
