# Document the menu-copy exception from docs question 4

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions), question 4.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md); awaits review. Label: `steward`.

## Recommendation

Keep the tested clipboard behavior and date ADR 0048's menu exception.

## Work

1. Explain that a refused menu copy reports failure and keeps the menu open without selecting text.
2. Retain manual text selection for refused keyboard and status-path copies, including the exact refused value.
3. Cite commit 45a78db0 and the menu-refusal and keyboard-refusal tests in static/tests/test_ui.py; preserve the original ADR reasoning.

## Acceptance

The ADR describes the tested distinction and no clipboard behavior changes. Server docs tests and the existing focused copy checks pass.
