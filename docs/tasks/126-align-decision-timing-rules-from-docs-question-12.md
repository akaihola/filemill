# Align decision timing rules from docs question 12

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md?f#questions), question 12.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md?f); approved by the user on 2026-10-20 (question 12). Label: `steward`.

## Recommendation

Record a behavior or port decision in the same change, not merely on the same day.

## Work

1. Replace [ROADMAP](../../docs/ROADMAP.md?f)'s same-day wording with a link to the architecture review's same-change rule.
2. Preserve [CONTRIBUTING](../../CONTRIBUTING.md?f)'s same-commit documentation requirement.
3. Keep historical decision dates and measurements intact; this is a policy wording correction.

## Acceptance

The three current documents no longer allow a behavior change to land before its required explanation. Server docs tests pass; no behavior changes.

## Result, 2026-10-20

- [ARCHITECTURE-REVIEW](../ARCHITECTURE-REVIEW.md#rules-for-changes) now
  requires an ADR in the same change for a decision that changes a port or a
  behaviour. Before, its rule named behaviour only, so the port scope came
  from ROADMAP alone.
- [ROADMAP](../ROADMAP.md#how-we-keep-it-this-way) no longer says "the same
  day". Its rule says "in the same change" and links to the review's rules for
  changes.
- [CONTRIBUTING](../../CONTRIBUTING.md#commits) is unchanged. It still requires
  the documentation in the same commit as the change.
- Historical dates and measurements are unchanged. The only other "same day"
  text, in `docs/testing/remaining-red-tests.md`, records history, not policy.

## Validation

- Red: `test_decision_records_arrive_with_the_change` failed on the review's
  behaviour-only rule before the wording change.
- Green: all 23 tests in `server/tests/test_docs.py` and all 11 in
  `server/tests/test_suppression_links.py` pass. In the sandbox, the
  portability guard fails on an unreadable `.claude/loop.md`; it passes
  outside the sandbox.
- Ruff check and Ruff format pass for the changed test file. No code or
  behaviour changes.
