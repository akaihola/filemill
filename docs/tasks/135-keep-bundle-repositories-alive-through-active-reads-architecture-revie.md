Steward issue, 2026-10-20 22:30. Goal: agentic-leverage (filemill is tier 1). Estimated 0.5 h.

Draft A14 of [the re-checked architecture review](../ARCHITECTURE-REVIEW.md#a14-bundle-eviction-removes-an-active-repository) (filemill [132], 2026-10-20): the eight-entry cache owns the temporary repositories made from Git bundles, while a request keeps only their paths. An eviction in the middle of a read can turn a live read into an empty tree or a missing member.

## Work

Retain the cached temporary directory's owner until every Git call for that request has finished. Keep cleanup tied to ownership and to the existing bounded cache. Surface a genuine Git command failure through the error path described under A7, without implementing the rest of A7.

## Acceptance

- Failing regressions first that evict the acquired entry before a tree read, and between a blob's metadata and content calls. Both reads then finish with correct data, and the directory disappears only after its last owner releases it.
- A concurrent-request case is covered; read-only behaviour and command deadlines are unchanged.
- ADR 0073 states the lifetime rule; the review's A14 entry says it is resolved.
- The suites you touched pass, under the memory rule: wait up to 10 minutes for 2 GiB `MemAvailable`, start at 1.5 GiB or more, stop below 1 GiB or on 512 MiB of swap growth, one suite at a time.
