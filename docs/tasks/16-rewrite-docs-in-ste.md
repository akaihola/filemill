---
depends-on: [14, 15]
---

# Rewrite the remaining documents in Simplified Technical English

## Goal

Every Markdown file uses Simplified Technical English (ASD-STE100). There
are fewer lines of prose than lines of code. Roadmap phase 2, step 7.

## The STE rules to apply

- One sentence gives one fact or one instruction.
- Keep sentences under 20 words. Use the active voice.
- Use one word for one meaning. Do not use a synonym for variety.
- Use the imperative for instructions: "Run the tests."
- Do not use "should", "may" or "might" for a rule. Use "must" or "do not".
- Delete text that does not help the reader do the task.
- Keep code names, paths and commands exact.

## Steps

1. List the files: `git ls-files '*.md'`.
2. Skip files that are already in STE: `docs/GOALS.md`, `docs/ROADMAP.md`,
   `docs/ARCHITECTURE-REVIEW.md` and the ADR files.
3. Rewrite each other file. Delete duplicated explanations. Keep one copy.
4. Measure: `git ls-files '*.md' | xargs cat | wc -l` and
   `git ls-files '*.py' '*.js' '*.css' | xargs cat | wc -l`.

## Done when

- The Markdown line count is below the code line count.
- Each claim in a document can be checked against the code with a `grep`.

## Scope

All `*.md` files. Do not change code.
