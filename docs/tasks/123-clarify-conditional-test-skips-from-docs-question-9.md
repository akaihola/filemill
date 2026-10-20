# Clarify conditional test skips from docs question 9

Source: [docs check], question 9.
Proposed by [plain answers]; approved by the user on 2026-10-20 (question 9). Label: `steward`.

## Recommendation

Require issue links for disabled work or defect skips; allow explicit platform and optional-tool prerequisite skips.

## Work

1. Narrow the [roadmap policy] with the Linux pipe-capacity and missing-Git examples.
2. Keep a reason on every prerequisite skip. Require an issue link when a test for supported behavior is disabled because it is broken or unfinished.
3. State that CI must supply required prerequisites and run the applicable checks. Do not use missing dependencies to obtain a misleading pass.

## Acceptance

The three cited skips have a clear policy classification, and the rule still forbids untracked disabled tests. No skip conditions change; server docs tests pass.

## Implementation — 2026-10-20

The [roadmap policy] now classifies the Linux pipe-capacity skip as a platform
prerequisite and both missing-Git skips as optional-tool prerequisites. Each
requires a reason. Disabled tests for broken or unfinished supported behavior
still require issue links. CI must supply required prerequisites and run the
applicable checks. No skip conditions changed.

Validation: the policy acceptance check failed against the old blanket rule
and passed after the clarification. All 21 [server docs tests] passed with
`uv run --project server pytest -q server/tests/test_docs.py`.
All seven pre-commit hooks passed with `uvx pre-commit run --all-files`.

[docs check]: 109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions
[plain answers]: 115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md
[roadmap policy]: ../ROADMAP.md#how-we-keep-it-this-way
[server docs tests]: ../../server/tests/test_docs.py
