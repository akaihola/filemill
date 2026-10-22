Steward issue, 2026-10-22 07:16 refill (steward decisions D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Estimated 1 h.

This is draft D1 of [the 2026-10-22 architecture review](../reviews/2026-10-22-architecture-review.md#draft-issues), filed as written there; read that draft and the finding it cites before starting. The review's line numbers refer to the commit it names; recheck them on current `main`.

## Work

Move the meaningful parser fixtures to tests that exercise the registered JavaScript VTT renderer, then remove Python `parse`, its helpers, `default_fmt` and `render_preview`. Keep the small empty-listing provider and its registration, and update the provider test/source map.

## Acceptance

- Timestamps, voices, YouTube metadata and blank payloads, malformed input and source preservation keep coverage on the live implementation.
- Ordinary VTT listing, raw bytes, empty virtual listing and suffix URLs keep their responses.
- No application code calls the deleted renderer; no cross-language parser generator replaces it.
- Update the A12 entry in [the architecture review][architecture] to say what is done.

## Ground rules

- Behaviour stays the same unless the acceptance below says otherwise. Write the failing or pinning test first where the draft asks for one.
- Run at most one focused test command at a time, under your launch prompt's memory rule; no full browser suite.
- Keep private paths and host names out of committed files (the docs tests reject them).
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker](../../TASKS.md).

## Implementation plan

1. Pin the live registered JavaScript renderer with the meaningful Python
   fixtures. Pin the provider registration and HTTP responses before deletion.
2. Remove the unreachable Python parser and renderer. Keep the empty-listing
   provider and registration. Update A12 and the source/test map together.
3. Run focused browser, provider and documentation checks and the quality gate,
   one command at a time with memory monitoring. Rebase and merge to main,
   then complete the tracker entry pending acceptance.

This removes no reachable behavior or port, so no new ADR is needed.

[architecture]: ../ARCHITECTURE-REVIEW.md#a12-smaller-defects-dead-code-and-audits
