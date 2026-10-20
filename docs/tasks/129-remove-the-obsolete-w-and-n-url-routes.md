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
- Recorded ADR 0088, the task 35 replacement date and the collision boundary
  with [121]. Updated current guidance and rebuilt the static bundle.

Validation so far: 519 resource/API/PWA/public-mode checks passed; both new
browser cases passed; the model checks and all seven pre-commit hooks passed.
Full browser and static-edition suites are in progress.
