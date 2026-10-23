Steward issue, 2026-10-23 14:00 tick (steward decisions D7 and D95). Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 20 min. Unlabelled.

This is draft D5 of the steward's Filemill recheck of 2026-10-23 (`<steward-vault>/log/2026-10-23-filemill-held-rechecks.md`, sections "Documentation review" and "Draft issues"). It holds the acceptance of [[146]](146-check-filemill-s-readme-contributor-docs-goals-and-roadmap-against-cur.md).

## Why

The symlink-documentation probe fails: [the static agent guide](../../static/AGENTS.md) calls the package UI directory a symlink to itself. [146]'s documentation review introduced this wording; the repository-root [UI link](../../ui/) is the actual symlink. The ordinary link check passes because both wrong links resolve.

## What to do

Restore the source label and relative destination to the repository-root UI symlink in that one sentence, keeping the target link at the package UI directory. Add a focused documentation assertion that follows the stated source/target relationship rather than merely checking that destinations exist.

## Constraints

- Documentation and its test only: `static/AGENTS.md`, the new assertion in `server/tests/test_docs.py` and this task's records. A formatting-only change that a required check demands is allowed.
- Keep private paths and host names out of committed docs and code (`test_documentation_uses_portable_development_examples`); the check receipt is exempt.
- Follow your launch prompt's memory rule.

## Acceptance

- The stated source is a symlink resolving to the stated target.
- The new semantic documentation check, the existing documentation and review-condition tests and the quality gate pass, run as CONTRIBUTING.md says.
- No production behaviour changes.
- Handoff: a short outcome; details stay in this task record.

Tracker: [Filemill's tracker](../../TASKS.md).

## Implementation, 2026-10-23

Corrected the source label and destination in [the static agent guide] to
name the repository-root [UI symlink], retaining the package target. The new
[semantic documentation test] extracts both links from that sentence, checks
that the source is a symlink, resolves both paths strictly and checks both
labels. No production behavior changed. No architecture finding changed status.

The test first failed because the stated package directory was not a symlink.
After the correction, all 35 documentation and review-condition tests passed.
The quality gate passed with Deno 2.6.8. Hook installation was attempted but
refused because `core.hooksPath` was configured; the existing setting was kept.

## Memory reports before merge

- **red:** `timeout 600 uv run --project server pytest -q server/tests/test_docs.py -k static_guide_ui_symlink_matches_checkout` — started at once; waited 0.0 s; admission/final MemAvailable 2432/2469 MiB; starting swap 2621 MiB; swap growth 8 MiB (peak 10 MiB); elapsed 6.0 s; exit 1.
- **docs:** `timeout 600 uv run --project server pytest -q server/tests/test_docs.py server/tests/test_review_conditions.py` — started at once; waited 0.0 s; admission/final MemAvailable 2334/2395 MiB; starting swap 2644 MiB; swap growth -10 MiB (peak 0 MiB); elapsed 30.1 s; exit 0.
- **gate:** `timeout 1800 uvx pre-commit run --all-files` — started at once; waited 0.0 s; admission/final MemAvailable 2408/2470 MiB; starting swap 2643 MiB; swap growth -25 MiB (peak 0 MiB); elapsed 29.1 s; exit 0.

[the static agent guide]: ../../static/AGENTS.md
[UI symlink]: ../../ui/
[semantic documentation test]: ../../server/tests/test_docs.py

## Merged verification

Base commit: `062e89e7c314a910df7ebb32be1599e58c5fe1c0`. Merged commit: `0d753d4a13dfea34ae9a14823573f35d993badf8`.
Delivery commits, oldest first: `0d753d4a13dfea34ae9a14823573f35d993badf8`.

The detached task checkout was clean at the merged commit. Both recorded
checks passed: all 35 documentation and review-condition tests, and the full
quality gate. The gate used an external mypy cache to keep the checkout clean.
The [check receipt] records the commands, lockfile hash, editable checkout
revision and results. No deployment is needed for this documentation-only fix.

- **record-docs:** `uv run <evidence-script> record <receipt> 'filemill [159]' docs` — started at once; waited 0.0 s; admission/final MemAvailable 2560/2572 MiB; starting swap 2600 MiB; swap growth 2 MiB (peak 2 MiB); elapsed 3.0 s; exit 0.
- **record-gate:** `uv run <evidence-script> record <receipt> 'filemill [159]' gate` — started at once; waited 0.0 s; admission/final MemAvailable 2505/2806 MiB; starting swap 2604 MiB; swap growth 1 MiB (peak 26 MiB); elapsed 30.1 s; exit 0.

[check receipt]: 159-describe-the-root-ui-symlink-correctly-in-static-agents-md-and-test-th.evidence.json
