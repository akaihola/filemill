---
depends-on: [162]
---

Steward issue, 2026-10-23 14:00 tick (steward decisions D7 and D95). Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 45 min. Unlabelled. Depends on [[162]](162-migrate-the-remaining-preview-api-consumers-to-raw-bytes-and-the-brows.md), the preview API migration.

This is draft D4 of the steward's Filemill recheck of 2026-10-23 (`<steward-vault>/log/2026-10-23-filemill-held-rechecks.md`, sections "Stylesheet cleanup" and "Draft issues"). It holds the acceptance of the tracker item "Delete `server/src/filemill/styles.py` …".

## Why

The obsolete stylesheet and `APP_CSS` pins are gone and the shell links shared CSS, but the request's "no other preview HTML route" condition still fails at the retained preview API.

## What to do

After the preview API migration, add the narrow route-contract check that the stylesheet cleanup never supplied. Assert shell-owned document presentation and raw bytes for file and member access, while keeping the expected HTML error responses. Leave the already-removed stylesheet and shared CSS implementation alone; record this prerequisite separately from the deletion itself.

## Constraints

- Tests and this task's records only; no production change beyond what the migration already made.
- Follow your launch prompt's memory rule.
- Keep private paths and host names out of committed docs and code (`test_documentation_uses_portable_development_examples`); the check receipt is exempt.

## Acceptance

- The stylesheet request probe and the new route-contract tests pass: the obsolete stylesheet and `APP_CSS` pins stay absent, the shell uses shared CSS, and no separate server preview renderer remains.
- The existing resource-route and preview regressions pass.
- Handoff: a short outcome; details stay in this task record.

Tracker: [Filemill's tracker](../../TASKS.md).
