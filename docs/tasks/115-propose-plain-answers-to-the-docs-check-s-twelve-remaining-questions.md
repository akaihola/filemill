Steward issue, 2026-10-19 21:00. Goal: agentic-leverage (review load); filemill
is tier 1. Labelled `review`.

[[109]](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md)'s
docs check ended with 13 questions where it couldn't tell whether the code or
the text is wrong (its "Questions" section). Antti found them too technical to
answer as they stand. Question 1, the unsandboxed archive HTML preview, is
filemill [[114]](114-sandbox-html-previews-of-archive-members-as-security-md-promises.md);
answer the other twelve.

## What to do

For each of questions 2–13, from the code, tests, ADRs and `git log`:

1. Recommend an answer, and say whether the code or the text should change.
2. Give the evidence in one or two sentences.
3. Write a one-sentence version of the question for Antti in everyday words,
   with no file names or line numbers, ending with the recommended answer.

Put the result under a new heading "Proposed answers, 2026-10-19" in [109]'s
task file. Make no code or doc changes besides that; for each answer that
needs a change, draft an issue under `## Unverified proposals`, labelled
`steward`.

## Acceptance

- Twelve proposed answers, each with evidence and a plain one-sentence version.
- Every drafted issue names the question it comes from.
- No push; the server suite's docs tests still pass.
