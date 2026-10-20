Steward issue, 2026-10-20 22:30. Goal: agentic-leverage (filemill is tier 1). Estimated 0.5 h.

Draft A13 of [the re-checked architecture review](../ARCHITECTURE-REVIEW.md#a13-json-column-refresh-keeps-the-old-parsed-value) (filemill [132], 2026-10-20): the JSON column's refresh rebuilds from a value parsed earlier, so an edit made outside Filemill stays invisible while the UI reports no change.

## Work

Give the virtual JSON adapter ownership of invalidation: on refresh, read the backing file or archive member again before rebuilding the column's children. Don't teach the core every parser's fields. Coordinate with the navigation and preview invalidation described under A9, without implementing A9.

## Acceptance

- Failing regressions first, for an open JSON column after an external edit, a removed key, a parse failure and a changed archive member.
- The column's own refresh reads the source again, updates the preview and the selection, and reports a parse error instead of keeping stale values.
- Static and development modes and served mode agree.
- The relevant port decision and documentation describe the new behaviour; the review's A13 entry says it is resolved.
- The suites you touched pass, under the same memory rule as filemill's other steward issues: wait up to 10 minutes for 2 GiB `MemAvailable`, start at 1.5 GiB or more, stop below 1 GiB or on 512 MiB of swap growth, one suite at a time.
