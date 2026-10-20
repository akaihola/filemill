# Clarify API path collisions from docs question 6

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions), question 6.
Proposed by [115](115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md); awaits review. Label: `steward`.

## Recommendation

Keep non-conflicting files under a folder named api accessible and correct the claim that the entire prefix is reserved.

## Work

1. Correct the resource-route comment in server/src/filemill/app.py and the docstring of test_named_route_wins_over_a_directory_of_the_same_name.
2. Extend route coverage to show /api/dir still resolves to the endpoint while /api/note.txt resolves to the fixture file; cover the directory listing too.
3. Distinguish these exact endpoint collisions from existing wildcard routes such as /ui/, /w/ and /n/. Do not broaden routing reservations.

## Acceptance

Focused resource-route and docs tests pass. Routing behavior stays unchanged; the test asserts the previously untested ordinary-file case.
