Steward issue, 2026-10-22 07:16 refill (steward decisions D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Estimated 1 h.

This is draft D2 of [the 2026-10-22 architecture review](../reviews/2026-10-22-architecture-review.md#draft-issues), filed as written there; read that draft and the finding it cites before starting. The review's line numbers refer to the commit it names; recheck them on current `main`.

## Work

Add a failing query-count regression, then derive the table schema and first-column uniqueness before the row loop in `server/src/filemill/providers/sqlite.py` and format keys from the result.

## Acceptance

- One table-schema query and at most two uniqueness queries per listing, independent of row count.
- Primary-key, composite-key and fallback labels, records, order and the 500-row marker are unchanged.
- Focused provider and API checks pass. Identity encoding is unchanged and no ORM is added.

## Ground rules

- Behaviour stays the same unless the acceptance below says otherwise. Write the failing or pinning test first where the draft asks for one.
- Run at most one focused test command at a time, under your launch prompt's memory rule; no full browser suite.
- Keep private paths and host names out of committed files (the docs tests reject them).
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker](../../TASKS.md).
