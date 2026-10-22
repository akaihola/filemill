Steward issue, 2026-10-22 07:16 refill (steward decisions D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Estimated 1 h.

This is draft D5 of [the 2026-10-22 architecture review](../reviews/2026-10-22-architecture-review.md#draft-issues), filed as written there; read that draft and the finding it cites before starting. The review's line numbers refer to the commit it names; recheck them on current `main`.

## Work

Add a deferred-load regression that mounts a new root while `walkPath` is waiting. Capture the originating file system and root, and check they are still current after each await and before the final state and render effects.

## Acceptance

- Releasing the old read changes no selection, path, focus or URL of the new root and issues no read through the replacement file system.
- Normal complete, truncated and declined-document walks still pass.
- The choose/refresh and preview-reuse guards stay; record in A9 that broader generation ownership remains open.

## Ground rules

- Behaviour stays the same unless the acceptance below says otherwise. Write the failing or pinning test first where the draft asks for one.
- Run at most one focused test command at a time, under your launch prompt's memory rule; no full browser suite.
- Keep private paths and host names out of committed files (the docs tests reject them).
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker](../../TASKS.md).
