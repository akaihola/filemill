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

- The stylesheet request probe and the new route-contract tests pass: the obsolete stylesheet and `APP_CSS` pins stay absent, the shell uses shared CSS, and no separate server preview renderer remains other than the narrowed reStructuredText route kept by [162]'s steward decision (2026-10-23 17:20); the route-contract tests assert that route answers 404 for every other kind.
- The existing resource-route and preview regressions pass.
- Handoff: a short outcome; details stay in this task record.

**Steward amendment, 2026-10-23 17:20.** [162] keeps `/api/preview` for
served reStructuredText only (its "Steward decision" section). Test that
contract here; the stylesheet item's "no other server route emits HTML"
stays unmet for that one route and waits for Antti.

Tracker: [Filemill's tracker](../../TASKS.md).

## Plan, 2026-10-23

- Add a request matrix for files and ZIP members across each preview kind.
  Assert shared-shell Rendered and Source views, exact raw bytes, and 404
  from the preview API except for reStructuredText.
- Keep HTML errors and the retained RST renderer. Probe the shared CSS
  request and the absence of the obsolete stylesheet and constant.
- Prove the matrix fails before [the migration], then run focused server
  regressions, migrated browser cases and the quality gate. Record checks
  again at the merged commit before completing the tracker move.

This is a test-only prerequisite receipt. It does not complete or accept the
separate stylesheet deletion item: the retained RST route still emits HTML
under the steward amendment. No architecture status or behavior changes;
[ADR 0094] remains the applicable decision.

[the migration]: 162-migrate-the-remaining-preview-api-consumers-to-raw-bytes-and-the-brows.md
[ADR 0094]: ../adr/0094-the-browser-renders-members-the-server-only-restructuredtext.md

## Results before merge, 2026-10-23

[The new route-contract tests] cover 22 suffixes as real files and ZIP
members. Their 44 cases check presentation and byte access together, plus
six HTML errors and one stylesheet request probe. Existing API tests cover
RST slices, oversized members, TAR and Git bundle members and SQLite rows.

- Red: applied only the new tests to the clean pre-migration commit
  `a40f6293`. All 42 non-RST file/member cases failed; 9 preservation checks
  passed. The old preview route did not return the required 404.
- Green: `timeout 600 uv run pytest -q
  server/tests/test_preview_route_contract.py
  server/tests/test_resource_routes.py server/tests/test_api.py
  server/tests/test_preview.py server/tests/test_docs.py
  server/tests/test_review_conditions.py` — 275 passed.
- Quality gate: `timeout 1800 uvx pre-commit run --all-files` — all seven
  hooks passed. No production files or shared CSS changed.
- Review: the request matrix covers each classifier branch, and HTML files
  are compared as bytes rather than incorrectly forbidden as HTML responses.
  No behavior or architecture finding changes, so no new ADR is needed.

[The new route-contract tests]: ../../server/tests/test_preview_route_contract.py

## Memory reports before merge

Each guarded command started at once, with a 0 s admission wait. Readings
are MiB; growth is final / peak. Exit 1 for red is expected.

| Command | Admission / final available | Start swap | Swap growth | Seconds | Exit |
| --- | --- | --- | --- | --- | --- |
| Pre-migration route matrix | 2826 / 2753 | 2373 | -1 / 0 | 19.0 | 1 |
| Focused green regressions | 2773 / 2802 | 2371 | 0 / 0 | 17.0 | 0 |
| Quality gate | 2744 / 2894 | 2362 | -97 / 0 | 29.1 | 0 |
