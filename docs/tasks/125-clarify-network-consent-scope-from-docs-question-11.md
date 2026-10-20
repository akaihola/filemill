# Clarify network consent scope from docs question 11

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions), question 11.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md); awaits review. Label: `steward`.

## Recommendation

Make GOALS' consent claim match the renderer-download switch and explicitly describe document resource requests.

## Work

1. Align the blanket non-goal with GOALS' privacy paragraph, README and ADR 0036: the remembered switch defaults on and controls third-party renderer downloads.
2. State that document images and other referenced resources may contact external hosts outside that switch. Preserve the no-telemetry rule and the statement that local folder reads stay in the browser.
3. Link to one current explanation. Do not describe the switch as a general network blocker or implement a new external-resource permission system under this documentation issue.

## Acceptance

The documentation gives the same explicit boundary everywhere it discusses consent. Server docs tests pass; renderer-consent behavior and tests remain unchanged.
