Steward issue, 2026-10-23 10:43 refill (steward decisions D94 and D95). Goal: agentic-leverage (filemill is tier 1). Estimated 30 min.

## Why

Two small documentation gaps remain after this week's reviews.

1. Filemill [157] added [the architecture summary](../ARCHITECTURE-SUMMARY.md) and pointed AGENTS.md at it, so workers read 5 KB before the 50 KB [architecture review](../ARCHITECTURE-REVIEW.md). [CONTRIBUTING.md](../../CONTRIBUTING.md) still says "Read the [architecture review] before implementation" (its "Read the" paragraph after the Markdown highlighting rules); [157]'s file scope excluded it (see "Follow-up for the steward" in [157]'s record).
2. Filemill [15] requires every ADR split from the old decisions table to stay under 40 lines. A 2026-10-23 recheck found [ADR 0020](../adr/0020-pvtoken-guards-preview-fills.md) and [ADR 0050](../adr/0050-history-pushes-on-entering-a-column-rewrites-otherwise.md) at 43 lines each, which holds [15]'s acceptance. [15] is over seven days old and later commits touched these files, so the acceptance policy asks for a fix-forward rather than a revert.

## What to do

1. In CONTRIBUTING.md, change that sentence to match AGENTS.md: read the summary first, then the review's sections that the change touches, by heading. Add the summary's link definition beside the existing ones.
2. Bring ADR 0020 and ADR 0050 to 39 lines or fewer each without dropping a fact, number or link. Tighten wording; keep the Context, Decision, Measurement and Consequences headings. `git log -p` on each file shows which later additions pushed it over.

Change nothing else.

## Constraints

- Documentation only: `CONTRIBUTING.md`, the two ADR files and this task's own records. A formatting-only change that a required check demands is allowed.
- Keep private paths and host names out of committed docs and code (`test_documentation_uses_portable_development_examples`); the check receipt is exempt.
- Follow your launch prompt's memory rule.

## Acceptance

- CONTRIBUTING.md points at the summary first and at the review by section, consistent with AGENTS.md.
- `wc -l` reports 39 or fewer lines for each of the two ADRs, and every fact, number and link they held before is still there (say so in this task record, with before and after line counts).
- `server/tests/test_docs.py` passes, run as CONTRIBUTING.md says.
- `git diff --stat` of the delivery lists only `CONTRIBUTING.md`, the two ADRs and this task's records.
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker](../../TASKS.md).

## Implementation plan, 2026-10-23

- Point the [contributor guide] at the summary first, then review sections by heading.
- Tighten both ADRs while preserving every fact, number, link and required heading.
- Verify line counts, content preservation, documentation tests and delivery scope;
  merge and record checks before completing the tracker entry.

[contributor guide]: ../../CONTRIBUTING.md
