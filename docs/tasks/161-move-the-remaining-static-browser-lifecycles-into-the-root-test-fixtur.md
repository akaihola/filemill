Steward issue, 2026-10-23 14:00 tick (steward decisions D7, D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 1.5 h. Unlabelled.

This is draft D2 of the steward's Filemill recheck of 2026-10-23 (`<steward-vault>/log/2026-10-23-filemill-held-rechecks.md`, sections "Shared browser fixtures" and "Draft issues"). It holds the acceptance of the tracker item "Run the static and server browser tests through one root `conftest.py` and one Playwright …".

## Why

The request probe still finds `async_playwright`, a Chromium launch and a persistent-context launch in [the static fixture module](../../static/tests/conftest.py). The keyboard suite now uses the shared root browser and has no CDN proxy, but the requested root lifecycle ownership is not complete.

## What to do

Move ordinary asynchronous and persistent-profile browser lifecycle ownership into root fixtures alongside the synchronous fixture. Keep static page construction and fake filesystem setup local. Preserve separate sync and async API adapters, native driver selection, per-test isolation and the persistent profile that folder-handle restoration needs; don't force incompatible event loops through one object.

## Constraints

- Test infrastructure only; no production code change.
- Follow your launch prompt's memory rule; the browser suites are heavy, so run one at a time.
- Keep private paths and host names out of committed docs and code (`test_documentation_uses_portable_development_examples`); the check receipt is exempt.

## Acceptance

- A source guard finds browser lifecycle startup only in the root fixture owner, and every suite consumes it.
- The six root shards, the static development suite, the folder-restoration checks and the independent collection checks pass, without weakened assertions or restored CDN proxy plumbing.
- Handoff: a short outcome; details stay in this task record.

Tracker: [Filemill's tracker](../../TASKS.md).
