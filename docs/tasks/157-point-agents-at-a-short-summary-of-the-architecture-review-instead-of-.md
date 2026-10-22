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

## Record

2026-10-22, implemented on the task branch.

### Changes

- [server/tests/test_docs.py](../../server/tests/test_docs.py):
  `test_architecture_summary_indexes_every_review_section` requires
  [the summary](../ARCHITECTURE-SUMMARY.md) to exist, to be at most 6,144
  bytes, and to name every `##` and `###` heading of
  [the review](../ARCHITECTURE-REVIEW.md) after its `## Section index`
  heading.
- [docs/ARCHITECTURE-SUMMARY.md](../ARCHITECTURE-SUMMARY.md), 5,469 bytes:
  principles (including the rules for changes), a module map, and 24 index
  lines, one per review heading. Each finding line gives its ID, title,
  status and priority, then the topics that make the section relevant.
- [AGENTS.md](../../AGENTS.md): read the summary first, then the review's
  sections that the issue touches, by heading. The alignment, scope and
  status-update rules remain; status updates now include the index line.
- [The review](../ARCHITECTURE-REVIEW.md): one added bullet under "How to
  read this review" naming the summary. Nothing else changed.

### Red-green evidence

- Red before the summary existed:
  `uv run pytest server/tests/test_docs.py -k architecture_summary -q`
  failed with `AssertionError: docs/ARCHITECTURE-SUMMARY.md is missing`.
- Green after adding it: the same command passed (1 passed).
- Red again with an unindexed heading: appending
  `### A15. Probe heading without an index line` to the review made the test
  fail with `The summary's section index omits ['A15. Probe heading without
  an index line']`. `git checkout -- docs/ARCHITECTURE-REVIEW.md` reverted
  the probe before the one-line review edit.

### Checks on the task branch

- `uv run pytest server/tests/test_docs.py -q`, run as
  [CONTRIBUTING.md](../../CONTRIBUTING.md) directs for documentation-only
  work: 28 passed. Inside Claude Code's sandbox the portability guard fails
  reading a sandbox-masked file, so it ran with the sandbox off.
- `uv run --project server ruff format --check server/src server/tests` and
  `uv run --project server ruff check server`: clean.
- No guarded heavy command ran before the merge; the docs tests take
  seconds.

### Follow-up for the steward

- [CONTRIBUTING.md](../../CONTRIBUTING.md) still says "Read the
  [architecture review] before implementation". This task's file scope
  excluded it; pointing it at the summary is a one-line change.

### Checks at the merged commit

Fast-forwarded `main` from `08c73874` to `760eee71` (one delivery commit,
`760eee71`). Each check below was recorded with the steward's
`check-evidence.py record` from a clean checkout detached at `760eee71`; the
receipt is
[157-point-agents-at-a-short-summary-of-the-architecture-review-instead-of-.evidence.json](157-point-agents-at-a-short-summary-of-the-architecture-review-instead-of-.evidence.json).
All six passed:

- `docs-tests`: `uv run pytest server/tests/test_docs.py -q`, 28 passed,
  including the new test.
- `summary-size`: the summary is 5,469 bytes, under 6,144.
- `unindexed-heading-fails`: in a temporary copy of the test and both
  documents, an added `### A15` heading without an index line makes the new
  test fail with `omits ['A15. Probe heading without an index line']`.
- `agents-points-at-summary`: AGENTS.md names the summary first, the review
  sections by heading, the summary's index lines, and the unchanged
  alignment and scope rules.
- `delivery-files`: the delivery diff lists only AGENTS.md, the review (one
  added line), the summary, `server/tests/test_docs.py` and this record.
- `python-format-lint`: `ruff format --check` and `ruff check` clean.

No deployment step applies: the change is documentation and one test, and
the served Filemill code is unchanged.

### Memory reports for the record calls

Each record call ran alone under a guard that required 2 GiB `MemAvailable`
to start and would stop it below 1 GiB or at 512 MiB swap growth.

| Check | Outcome | Admission / final MemAvailable | Swap start / growth | Elapsed | Exit |
| --- | --- | --- | --- | --- | --- |
| docs-tests | started at once, no wait | 2,232 / 2,311 MiB | 2,861 / 2 MiB | 14 s | 0 |
| summary-size | started at once, no wait | 2,311 / 2,195 MiB | 2,863 / 0 MiB | 2 s | 0 |
| unindexed-heading-fails | started at once, no wait | 2,285 / 2,154 MiB | 2,863 / −1 MiB | 8 s | 0 |
| agents-points-at-summary | started at once, no wait | 2,154 / 2,218 MiB | 2,862 / 14 MiB | 4 s | 0 |
| delivery-files | started at once, no wait | 2,213 / 2,243 MiB | 2,876 / 0 MiB | 1 s | 0 |
| python-format-lint | started at once, no wait | 2,241 / 2,156 MiB | 2,876 / 0 MiB | 2 s | 0 |
