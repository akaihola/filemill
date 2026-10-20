# Align decision timing rules from docs question 12

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions), question 12.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md); awaits review. Label: `steward`.

## Recommendation

Record a behavior or port decision in the same change, not merely on the same day.

## Work

1. Replace ROADMAP's same-day wording with a link to the architecture review's same-change rule.
2. Preserve CONTRIBUTING's same-commit documentation requirement.
3. Keep historical decision dates and measurements intact; this is a policy wording correction.

## Acceptance

The three current documents no longer allow a behavior change to land before its required explanation. Server docs tests pass; no behavior changes.
