Steward issue, 2026-10-22 06:17 refill (steward decisions D53 and D95: whole-repository architecture review aimed at simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Label `review`. Estimated 1.5 h.

filemill is the most active repository (239 commits on `main` since 2026-10-19) and has never had a whole-repository architecture review. Its [2026-10-22 docs review](../reviews/2026-10-22-docs-review.md) and [2026-10-21 security review](../reviews/2026-10-21-security-review.md) already cover docs and security.

## Work

1. Read `README.md`, `AGENTS.md`, `CONTRIBUTING.md` and `docs/`, then `server/`, `ui/`, `static/` and `native/`, and the tests.
2. Apply the `honey` principles (speculative generality, hand-rolled stdlib, single-caller abstractions, dead code, narration) and the `codebase-design` deep-module vocabulary, using those skills if your session has them: where a seam would make a module smaller to change and easier to test, where two code paths do the same job (for example served and browser-owned folders), and what can be deleted.
3. Write `docs/reviews/2026-10-22-architecture-review.md`: findings ranked by benefit per hour, each with file and line evidence on `main`, what changes if it is fixed, and a drafted issue (title, work, acceptance, about an agent hour each). Mark drafts that overlap open issues in `TASKS.md` (including In Progress [130] and [141]) or findings of the two reviews above instead of duplicating them.

## Ground rules

- Architecture only. Don't probe for vulnerabilities or write exploit reproductions.
- Read-only apart from the report and this issue's tracker moves. Don't file the drafts; the steward files them.
- Run no browser suite; at most one focused test command at a time, under your launch prompt's memory rule.
- Keep private paths and host names out of the report (the docs tests reject them).

## Acceptance

- Every finding cites code on `main` and says what changes if it is fixed.
- The report ends with a `## Draft issues` section and names the three drafts to do first, and why.
- The repository's documentation tests still pass with the new report.
- Handoff: a short outcome; details go in the report and this task record.

Tracker: [the filemill tracker](../../TASKS.md).
