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

## Delivery, 2026-10-23

The [contributor guide] now reads the [architecture summary] first and selects
[architecture review] sections by heading, matching the agent instructions.
[ADR 0020] and [ADR 0050] each went from 43 to 39 lines. A comparison against
the originals confirms that every fact, number and link remains. Context,
Decision, Measurement and Consequences headings remain in both ADRs.

The preview key, metadata and revision lifecycle, invalidation, focus, object-URL
lifetime and open A9 limitations remain. The history key, input-specific push or
rewrite rules, shared-edition repair, pending/declined column behavior, loading
UI, Back sequence and controlled-response regression remain.

## Validation before merge

- Focused acceptance assertions failed first on the original contributor
  instruction, then passed after the edits. They verify summary-first guidance,
  review selection by heading, both line limits, identical reference definitions,
  identical number sequences and all four required headings.
- `wc -l`: 39 lines for each ADR.
- `timeout 600 uv run --project server pytest -q server/tests/test_docs.py server/tests/test_review_conditions.py`:
  34 passed, following the contributor guide's testing index.
- `timeout 600 uvx pre-commit run --all-files`: all seven hooks passed.
- `git diff --check`: passed. Delivery scope is the contributor guide, the two
  ADRs and this task record only; tracker moves are separate task records.
- Documentation only: no port, behavior or architecture finding status changed.

## Memory reports before merge

- **docs:** `timeout 600 uv run --project server pytest -q server/tests/test_docs.py server/tests/test_review_conditions.py`; started at once; wait 0.0 s; admission 2535 MiB; final 2649 MiB; starting swap 2801 MiB; swap growth 22 MiB; elapsed 14.04 s; exit 0.
- **gate:** `timeout 600 uvx pre-commit run --all-files`; started at once; wait 0.0 s; admission 2658 MiB; final 2691 MiB; starting swap 2822 MiB; swap growth 35 MiB; elapsed 44.08 s; exit 0.

[architecture summary]: ../ARCHITECTURE-SUMMARY.md
[architecture review]: ../ARCHITECTURE-REVIEW.md
[ADR 0020]: ../adr/0020-pvtoken-guards-preview-fills.md
[ADR 0050]: ../adr/0050-history-pushes-on-entering-a-column-rewrites-otherwise.md

## Merged checks and completion

Base commit: `f9b0f74fe9f1f0c14343ab76262b7e63c0895e40`. Merged commit: `5a278dea7c0f77c68a0d817fd10e9fb322968ecf`.
Delivery commits, oldest first: `f0136c80fa2922abaf2984027080f0908db5a0d2`, `5a278dea7c0f77c68a0d817fd10e9fb322968ecf`.

Checks ran from a clean checkout detached at the merged commit. The shared
checkout stayed on main. The [check receipt] contains the exact commands,
lockfile hash, editable-checkout revision and results:

- **content:** passed; both ADRs are 39 lines, down from 43; summary-first
  instructions, review-by-heading selection, numbers, links and headings verified.
  The fact-by-fact review described above remains valid at the merged commit.
- **docs:** passed; 34 documentation and review-condition tests.
- **gate:** passed; all seven quality hooks.
- **scope:** passed; whitespace check and delivery diff list only the four
  permitted documents. The completion commit adds only this task's tracker
  status, updated record and receipt.

No deployment is needed for these documentation changes. No owner action or
agent follow-up remains. Completion leaves acceptance unchecked.

## Memory reports for recording

Each command below is one bounded `uv run` evidence-recorder call for
`filemill [158]`; exact commands are in the [check receipt].

- **Record content:** started at once; wait 0.0 s; admission 2568 MiB; final 2791 MiB; starting swap 2940 MiB; swap growth 0 MiB; elapsed 1.0 s; exit 0.
- **Record docs:** started at once; wait 0.0 s; admission 2871 MiB; final 2746 MiB; starting swap 3007 MiB; swap growth -3 MiB; elapsed 10.02 s; exit 0.
- **Record gate:** started at once; wait 0.0 s; admission 2848 MiB; final 2843 MiB; starting swap 2999 MiB; swap growth 0 MiB; elapsed 6.01 s; exit 0.
- **Record scope:** started at once; wait 0.0 s; admission 2572 MiB; final 2839 MiB; starting swap 2959 MiB; swap growth 2 MiB; elapsed 2.03 s; exit 0.

[check receipt]: 158-point-contributing-md-at-the-architecture-summary-and-trim-adrs-0020-a.evidence.json
