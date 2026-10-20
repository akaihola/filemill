# Explain dependency constraints from docs question 10

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md?f#questions), question 10.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md?f); approved by the user on 2026-10-20 (question 10). Label: `steward`.

## Recommendation

Clarify the policy and add evidence-based comments without changing dependency versions.

## Work

1. Distinguish minimum supported versions, deliberate bounded versions and exact lockfile selections in [GOALS](../../docs/GOALS.md?f).
2. Explain the build-backend range and conditional zstandard dependency where history or validation supports a reason; preserve the Playwright browser-match and mypy notes.
3. Check inherited development minimums against history. State when their compatibility rationale is unverified; do not claim minimum-version testing or invent a reason for every inherited floor.

## Acceptance

Every described reason has evidence or an explicit gap. No version specifier or lock resolution changes, no blanket pinning is added, and the server docs tests pass.
