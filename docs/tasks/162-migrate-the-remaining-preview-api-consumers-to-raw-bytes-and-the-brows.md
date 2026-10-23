Steward issue, 2026-10-23 14:00 tick (steward decisions D7, D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 2 h. Unlabelled.

This is draft D3 of the steward's Filemill recheck of 2026-10-23 (`<steward-vault>/log/2026-10-23-filemill-held-rechecks.md`, sections "Browser PPTX" and "Draft issues"). It holds the acceptance of the tracker item "Render `.pptx` in the browser …", and the stylesheet cleanup's follow-up depends on it.

## Why

The PPTX request probe confirms local slide-text extraction and the removal of the Python runtime renderer, but fails because the preview API still exists for other formats and virtual members.

## What to do

Inventory the remaining direct and virtual-member consumers of the preview API, then move only those consumers to the existing raw-byte access and browser renderer registry. Preserve RST heading slices, archive and member identity, source-versus-rendered behaviour, offline fallback and content limits before deleting the route. Keep this a renderer migration with no new framework. If a required capability can't be preserved, stop and record the exact unsupported case in this task record for the steward rather than deleting it.

## Constraints

- Follow your launch prompt's memory rule; the browser suites are heavy, so run one at a time.
- Keep private paths and host names out of committed docs and code (`test_documentation_uses_portable_development_examples`); the check receipt is exempt.

## Acceptance

- No preview-API route or client caller remains; the Python PPTX renderer and its runtime package stay absent.
- Real PPTX text, RST slice and archive-member regression tests pass, plus both browser modes (development and bundle), with no supported rendering capability removed.
- The root suite passes as CONTRIBUTING.md says.
- Handoff: a short outcome; details stay in this task record.

Tracker: [Filemill's tracker](../../TASKS.md).
