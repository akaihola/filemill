# Clarify deliberate test delays from docs question 8

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions), question 8.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md); awaits review. Label: `steward`.

## Recommendation

Clarify the no-fixed-waits rule to prohibit time-based guesses of readiness while allowing slow responses as test input.

## Work

1. Update ROADMAP Phase 7 and link to the condition-based waiting guidance in server/CONTRIBUTING.md.
2. Use test_declined_json_member_recovers_after_refresh as the example: its response delay supplies slow input, while loading/error and DOM conditions determine completion.
3. Describe test_browser_waits.py accurately as a guard against wait_for_timeout, not a ban on every sleep. A delay alone must not count as proof that two operations overlapped.

## Acceptance

The policy distinguishes test input from synchronization and does not excuse arbitrary readiness sleeps. Docs and browser-wait guard tests pass; no test delay or assertion is weakened.
