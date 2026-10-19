# Check filemill's docs and ADR statuses against the code, and fix what disagrees

Steward issue, 2026-10-19 (spare quota, steward decisions D48 and D53: review
of docs, docstrings, comments and task descriptions). Goal: agentic-leverage;
filemill is tier 1 and the most active repository: 575 commits on `main`
since 2026-09-19, 150 of them in the last week. Its `docs/` holds 83 ADRs,
`ROADMAP.md`, `GOALS.md`, `ARCHITECTURE-REVIEW.md` and the testing notes.

## Work

1. Read `README.md`, `SECURITY.md`, `docs/GOALS.md`, `docs/ROADMAP.md`,
   `docs/ARCHITECTURE-REVIEW.md` and `docs/testing/` against current `main`.
   List every statement the code contradicts, every stale command, path or
   setting, and every explanation duplicated across files, with the file and
   line of both sides.
2. Go through `docs/adr/`: find ADRs whose decision the code no longer
   follows, or that a later ADR replaced, without a status that says so.
   Mark each superseded with a link to what replaced it; don't rewrite its
   reasoning.
3. Check the docstrings and comments of the modules the docs describe for
   the same contradictions.
4. Fix the text where the code is clearly right. Where it's unclear whether
   the code or the text is wrong, don't guess: list it under "Questions" in
   this issue's description.
5. Where one section repeats another, keep one explanation and link to it.

## Ground rules

- Docs, docstrings and comments only: no behaviour, test or dependency
  changes.
- No host names or private paths in any file: the docs test rejects them.

## Acceptance

- `server/tests/test_docs.py` passes.
- Every fix listed in the description cites the code line it follows.
- The description lists what changed and the open questions.
