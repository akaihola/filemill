---
depends-on: [11]
---

# Correct the stale claims in the documents

## Goal

Every document describes the code as it is. `docs/ARCHITECTURE-REVIEW.md`,
finding 15, lists the wrong claims. Roadmap phase 0, step 5.

## Steps

Fix each claim below. Check the code before you write the new text.

1. `server/README.md`: it lists `/f/` URLs as a feature, counts 56 browser
   tests, and says the suite passes. Count the tests with
   `grep -c "^def test_\|^async def test_" server/tests/test_browser*.py`.
   Write the real state.
2. `server/CONTRIBUTING.md`: it states HTMX invariants and calls the cutover
   unfinished. Delete the HTMX text. Say that the shared UI is the only finder.
3. `server/TASKS.md`: it marks `/f/` as in progress and numbers two issues
   #46 and #47 twice, in conflict with `server/ISSUES.md`. Give each issue one
   number. Mark `/f/` as done or delete it.
4. `docs/tasks/2-fix-all-test-failures.md`: compare each claim with the
   current test output and correct it.
5. Root `TASKS.md`: the completed item "Text file editing should start with
   the cursor at the top of the file" fails. Move it back to the backlog, or
   delete it if task [12] has fixed it.

## Done when

- Each claim in the five files can be checked with a `grep` or a test run.
- No file says that HTMX is in use or that the cutover is unfinished.

## Scope

Documents only. Do not change code.
