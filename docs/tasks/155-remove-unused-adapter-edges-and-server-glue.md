Steward issue, 2026-10-22 08:54 refill (steward decisions D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Estimated 45 min.

This is draft D6 of [the 2026-10-22 architecture review](../reviews/2026-10-22-architecture-review.md#draft-issues), filed as written there; read that draft and finding F6 before starting. The review's line numbers refer to the commit it names; recheck them on current `main`, since [150] has since retired the Python WebVTT renderer.

## Work

Recheck callers, then remove the three dead imports, `_HTML_EXTS`, the unused integer conversion and the internal `is_vfs_file` helper. Retire tests that only assert the removed wrapper; keep the registry behaviour checks. Update the review's A12 remaining list; Source routing decisions stay with A8.

## Acceptance

- Development and bundled module graphs still load.
- Current string, default and path query dispatch and provider lookup tests pass.
- No replacement abstraction and no behaviour change.
- No service restart is needed; don't restart `filemill` or `filemill-public`.

## Ground rules

- Run at most one focused test command at a time, under your launch prompt's memory rule; no full browser suite.
- Keep private paths and host names out of committed docs and code (the docs tests reject them). The check receipt (`*.evidence.json`) is exempt.
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker](../../TASKS.md).

[150]: 150-retire-the-unreachable-python-webvtt-renderer-architecture-review-a12.md
