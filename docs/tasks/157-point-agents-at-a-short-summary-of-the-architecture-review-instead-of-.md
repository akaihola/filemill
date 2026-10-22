Steward issue, 2026-10-22 22:11 refill (steward decisions D94 and D95). Goal: agentic-leverage, tier 1. Estimated 45 min.

## Why

[AGENTS.md](../../AGENTS.md) tells every worker to read [the architecture review](../ARCHITECTURE-REVIEW.md) first, and the review is 50 KB. In paced sessions from 2026-10-20 to 2026-10-22 it put 0.90 M characters of truncated output into Codex workers' context and 0.24 M characters into Claude workers' through six large Reads: the largest single design-document source in the steward's attribution (`<steward-vault>/docs/reviews/2026-10-22-large-tool-outputs.md`, draft D3). Each such read stays in the worker's context for the rest of its session.

## What to do

1. Write the test first (this repository's red-green rule): in `server/tests/test_docs.py`, a test that the new summary is at most 6,144 bytes and that every `##` and `###` heading of `docs/ARCHITECTURE-REVIEW.md` appears in the summary's section index. Show it failing before the summary exists.
2. Add `docs/ARCHITECTURE-SUMMARY.md`, 6 KB or less: the principles and module map from "Architecture as it is" and "Rules for changes", then a section index with one line per heading of the review (each finding with its ID, title and status), saying when an issue should read that section.
3. Change the AGENTS.md paragraph to: read the summary first, then the review's sections that the issue touches, by heading. Keep its other rules unchanged: align changes with the proposed architecture, stay within the issue's scope, and update affected findings when the implementation changes their status (now also the summary's index line).
4. Optionally add one line to the review's "How to read this review" naming the summary. Change nothing else in the review.

## Constraints

- Documentation and the one test only; no other code. A formatting-only change that a required check demands is allowed.
- The findings, their statuses and the review's wording stay as they are.
- Keep private paths and host names out of committed docs and code (`test_documentation_uses_portable_development_examples`); the check receipt is exempt.
- Filemill [156] may be working on the test suite at the same time: touch only `AGENTS.md`, the new summary, `server/tests/test_docs.py`, at most one line of the review, and this task's own record.
- Follow your launch prompt's memory rule.

## Acceptance

- The summary is at most 6 KB and holds the principles, the module map and an index line for every heading of the review; AGENTS.md points at it as described in step 3.
- The docs tests pass, run as [CONTRIBUTING.md](../../CONTRIBUTING.md) says, including the new test. The record shows the new test failing before the summary, and failing again when a heading is added to the review without an index line (then reverted).
- `git diff --stat` of the delivery lists only the files named under Constraints.
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker](../../TASKS.md).
