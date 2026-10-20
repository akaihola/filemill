Steward issue, 2026-10-20 22:30. Goal: agentic-leverage (filemill is tier 1). Estimated 0.5 h.

Draft A14 of [the re-checked architecture review](../ARCHITECTURE-REVIEW.md#a14-bundle-eviction-removes-an-active-repository) (filemill [132], 2026-10-20): the eight-entry cache owns the temporary repositories made from Git bundles, while a request keeps only their paths. An eviction in the middle of a read can turn a live read into an empty tree or a missing member.

## Work

Retain the cached temporary directory's owner until every Git call for that request has finished. Keep cleanup tied to ownership and to the existing bounded cache. Surface a genuine Git command failure through the error path described under A7, without implementing the rest of A7.

## Acceptance

- Failing regressions first that evict the acquired entry before a tree read, and between a blob's metadata and content calls. Both reads then finish with correct data, and the directory disappears only after its last owner releases it.
- A concurrent-request case is covered; read-only behaviour and command deadlines are unchanged.
- ADR 0073 states the lifetime rule; the review's A14 entry says it is resolved.
- The suites you touched pass, under the memory rule: wait up to 10 minutes for 2 GiB `MemAvailable`, start at 1.5 GiB or more, stop below 1 GiB or on 512 MiB of swap growth, one suite at a time.

## Implementation, 2026-10-21

Tree and blob reads hold the cached temporary-directory owner through their
last Git call. Cache eviction releases only the cache's reference. The last
reader releases the directory. The cache still holds at most eight entries.
No lease manager or new dependency is required.

Git command failures now raise through the existing provider error path.
Listings report `denied`. Blob metadata uses `cat-file --batch-check` so a
missing member still returns 404. NUL-delimited input supports line breaks in
member names. Read-only operations, Git configuration isolation and the
60-second command deadline stay in place. [ADR 0073] records the lifetime
rule, and [A14] is resolved. The remaining A7 work is outside this change.

## Validation, 2026-10-21

- **Red:** Six new regression cases failed before the implementation. They
  covered eviction before a tree read, eviction between blob metadata and
  content, two active readers, and command exit, timeout and execution errors.
- **Green:** 149 tests passed across the bundle provider, API, VFS and
  documentation checks. Error cases cover initialization, unbundling and tree
  reads. Failed initialization removes its temporary directory. Two existing
  Docutils deprecation warnings remain.
- **Gate:** The full pre-commit gate passed: Ruff, formatting, mypy, Deno
  formatting and lint, suppression-link tests and bundle consistency.
- **Memory:** Suites ran one at a time under a monitor. Each run started with
  at least 2 GiB available. The final focused run stayed above 2.6 GiB; swap
  use decreased. The monitor stops below 1 GiB available or after 512 MiB of
  swap growth. No run reached a stop threshold.

[ADR 0073]: ../adr/0073-git-bundles-browse-by-refs-and-trees.md
[A14]: ../ARCHITECTURE-REVIEW.md#a14-bundle-eviction-removes-an-active-repository
