Steward issue, 2026-10-21 14:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Labelled `review`: an evidence search, routed to GPT (steward decision D68). Estimated 1 h. Source: the steward's triage of the review queue, `<steward-vault>/notes/2026-10-21-left-to-antti-triage.md`.


[43] (server browser baseline failures) waits in the review queue because nobody can say what it was about: its task lacks the original revision and nine of the eleven failing test names. Triage section "Prepare the specific repairs", item "Unidentified Filemill browser failures".

## Work

1. Search retained evidence for the revision and all eleven test names: [43]'s task file, `docs/reviews/`, `docs/ARCHITECTURE-REVIEW.md`, commit messages and the history of the test files around [43]'s dates. Don't substitute an unrelated passing suite.
2. If found, check out that revision in a disposable worktree, reproduce the failures, and classify each as fixed since, still failing, or obsolete.
3. If not recoverable, write down exactly what is missing and draft one retirement choice for Antti (what retiring [43] means, and what is lost).

## Acceptance

- [43]'s task file gains a dated note with the findings and either the classification or the retirement choice.
- No code change. Memory: follow your launch prompt's memory rule, and run one heavy command (test suite, browser, build) at a time.

## Execution plan, 2026-10-21

1. Trace [the baseline report] through retained documents, commit messages,
   tracker history and browser-test history, including all local Git refs.
2. Reproduce only a baseline supported by the evidence. If the revision or
   eleven-test inventory cannot be recovered, record the gaps and a retirement
   choice for Antti in that report.
3. Validate the documentation, merge to main, and complete this evidence search
   pending acceptance. Leave the baseline report's acceptance unchanged.

## Result, 2026-10-21

Completed the evidence search. [The dated findings] identify the report's first
record in `55d9267654a5ffaeb7faa195df629f2afcdb9b86` on September 5 and list
ten candidate test names: two legacy URL tests and eight mobile restore tests.
Neither tested revision nor the original eleven-node failure list was found.
The findings record the missing evidence and draft choice R1 for Antti: retire
the report without claiming all eleven failures were fixed. They state what
that decision loses. The decision remains unapplied, and the original issue
remains unaccepted.

No disposable baseline checkout or browser replay was made because no tested
revision was identified. No code or test files changed. [The architecture
review] now distinguishes this unidentified report from the later gate repairs.

### Validation

- **Documentation:** `uv run --project server pytest server/tests/test_docs.py -q`
  passed all 27 checks.
- **Required gate:** `uvx pre-commit run --all-files` passed all seven hooks,
  including the static bundle check.
- **Evidence checks:** parsed the historical keyboard source at `55d92676`;
  exactly ten tests enter legacy URLs, eight of them mobile. All ten names
  occur in the later TSV. Nine remain in the current source; the retired
  legacy-query test does not. These are source checks, not browser results.
- **Document checks:** all 105 local reference links in the three changed
  documents resolve; new task headings fit 60 characters. `git diff --check`
  passes. No current passing browser suite was substituted for the old run.

### Memory guard

Each guarded command ran alone, with a timeout and process-group cleanup.
Admission required 2,048 MiB available, with a 1,536 MiB fallback only after
ten minutes. The monitor checked every 0.25 seconds and would stop the process
group below 1,024 MiB available or above 512 MiB swap growth. No stop occurred.
All figures below are MiB; elapsed time is seconds. Swap growth is the final
change from admission; the largest sampled growth for these runs was 1 MiB.
The three search batches streamed Git output to scratch files.

| Guarded command | Outcome | Wait | Available, admission → final | Swap start | Swap growth | Elapsed | Exit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Git history search: task diff, messages, browser and tracker logs | started at once | 0 | 3312.93 → 3304.66 | 2301.88 | 0 | 3.02 | 0 |
| Git provenance search: report, route removal, browser port and review histories | started at once | 0 | 3388.62 → 3393.36 | 2304.46 | 0 | 0.50 | 0 |
| Git evidence search: report phrases, dated messages and artifact history | started at once | 0 | 3051.82 → 3052.08 | 2306.61 | -0.25 | 7.38 | 0 |
| Documentation pytest command above | started at once | 0 | 2930.38 → 2959.33 | 2294.36 | +0.50 | 33.82 | 0 |
| Pre-commit command above | started at once | 0 | 3071.00 → 2973.62 | 2294.61 | +1.00 | 28.63 | 0 |

[the baseline report]: 43-server-browser-baseline-failures.md
[The dated findings]: 43-server-browser-baseline-failures.md#recovery-findings-2026-10-21
[The architecture review]: ../ARCHITECTURE-REVIEW.md
