Steward issue, 2026-10-23 14:00 tick (steward decisions D7, D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 1 h. Unlabelled.

This is draft D1 of the steward's Filemill recheck of 2026-10-23 (`<steward-vault>/log/2026-10-23-filemill-held-rechecks.md`, sections "Shell representations" and "Draft issues"). It holds the acceptance of [[33]](33-shell-for-every-representation.md).

## Why

[33]'s required grep still finds Pygments and `render_source`, and Pygments remains a runtime dependency. Raw bytes and the render/highlight shell checks pass. The separate no-columns mismatch is an authorized supersession: [the accepted layout decision](../adr/0067-drop-no-columns-layout.md) and the accepted removal item require fallback to full-columns.

## What to do

Trace current `render_source` callers and remove the unused Python source-highlighting path, its obsolete tests and the runtime dependency once browser source coverage is confirmed. Keep the accepted no-columns removal and cite its supersession in [33]'s record with a dated note. The RST and archive-member preview API migration is a separate issue, [[162]](162-migrate-the-remaining-preview-api-consumers-to-raw-bytes-and-the-brows.md); don't delete its live consumers here. If a live caller remains that only that migration can remove, stop and say so in this record.

## Constraints

- Follow your launch prompt's memory rule; the browser suites are heavy, so run one at a time.
- Keep private paths and host names out of committed docs and code (`test_documentation_uses_portable_development_examples`); the check receipt is exempt.

## Acceptance

- [33]'s grep has no Pygments or `render_source` matches, and the runtime dependency is gone from `server/pyproject.toml` and the lock.
- Bare and raw byte and render/highlight shell tests pass, alongside the accepted no-columns fallback test.
- The root suite passes as CONTRIBUTING.md says.
- Handoff: a short outcome; details stay in this task record.

Tracker: [Filemill's tracker](../../TASKS.md).
