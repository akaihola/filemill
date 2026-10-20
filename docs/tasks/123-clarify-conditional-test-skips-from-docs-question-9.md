# Clarify conditional test skips from docs question 9

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions), question 9.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md); awaits review. Label: `steward`.

## Recommendation

Require issue links for disabled work or defect skips; allow explicit platform and optional-tool prerequisite skips.

## Work

1. Narrow ROADMAP's skipped-test rule with the Linux pipe-capacity and missing-Git examples.
2. Keep a reason on every prerequisite skip. Require an issue link when a test for supported behavior is disabled because it is broken or unfinished.
3. State that CI must supply required prerequisites and run the applicable checks. Do not use missing dependencies to obtain a misleading pass.

## Acceptance

The three cited skips have a clear policy classification, and the rule still forbids untracked disabled tests. No skip conditions change; server docs tests pass.
