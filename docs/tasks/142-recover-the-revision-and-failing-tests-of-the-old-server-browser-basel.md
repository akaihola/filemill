Steward issue, 2026-10-21 14:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Labelled `review`: an evidence search, routed to GPT (steward decision D68). Estimated 1 h. Source: the steward's triage of the review queue, `<steward-vault>/notes/2026-10-21-left-to-antti-triage.md`.


[43] (server browser baseline failures) waits in the review queue because nobody can say what it was about: its task lacks the original revision and nine of the eleven failing test names. Triage section "Prepare the specific repairs", item "Unidentified Filemill browser failures".

## Work

1. Search retained evidence for the revision and all eleven test names: [43]'s task file, `docs/reviews/`, `docs/ARCHITECTURE-REVIEW.md`, commit messages and the history of the test files around [43]'s dates. Don't substitute an unrelated passing suite.
2. If found, check out that revision in a disposable worktree, reproduce the failures, and classify each as fixed since, still failing, or obsolete.
3. If not recoverable, write down exactly what is missing and draft one retirement choice for Antti (what retiring [43] means, and what is lost).

## Acceptance

- [43]'s task file gains a dated note with the findings and either the classification or the retirement choice.
- No code change. Memory: follow your launch prompt's memory rule, and run one heavy command (test suite, browser, build) at a time.
