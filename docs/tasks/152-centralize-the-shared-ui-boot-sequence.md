Steward issue, 2026-10-22 07:16 refill (steward decisions D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Estimated 1 h.

This is draft D3 of [the 2026-10-22 architecture review](../reviews/2026-10-22-architecture-review.md#draft-issues), filed as written there; read that draft and the finding it cites before starting. The review's line numbers refer to the commit it names; recheck them on current `main`.

## Work

Replace the three identical initialization blocks (server, browser-owned and native hosts) with one core initializer; leave host-specific choices at the three call sites. Remove the narration about the retired classic-script loading order.

## Acceptance

- One implementation of the seven-call sequence; each host calls it once after creating its shell.
- Mount, keyboard, sorting and preview checks keep their behaviour; check the static development and bundle builds and the native composition through their existing entry points, rebuild the static bundle and keep its import and collision checks.
- No configuration class, event bus or host inheritance tree is added.

## Ground rules

- Behaviour stays the same unless the acceptance below says otherwise. Write the failing or pinning test first where the draft asks for one.
- Run at most one focused test command at a time, under your launch prompt's memory rule; no full browser suite.
- Keep private paths and host names out of committed files (the docs tests reject them).
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker](../../TASKS.md).
