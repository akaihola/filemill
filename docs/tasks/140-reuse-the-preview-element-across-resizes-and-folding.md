Steward issue, 2026-10-21 14:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 1.5 h. Source: the steward's triage of the review queue, `<steward-vault>/notes/2026-10-21-left-to-antti-triage.md`.


[21] (cache the preview element) waits in the review queue because its central guarantee is missing: resizing the window or folding the tree still renders the preview again. Triage section "Prepare the specific repairs", item "Filemill preview reuse".

## Work

1. Keep the rendered preview for the same file and metadata across resizes and folding.
2. Invalidate it when the file is edited, its metadata changes or the selection moves.
3. Add tests that count preview renders.

## Acceptance

- Resizing and folding cause no extra preview rendering; an edit or a selection change renders once.
- The existing rendering budgets and editor invalidation checks pass, with the suites the Rules name.
- Add a dated pointer to this issue's evidence in [21]'s task file. Memory: follow your launch prompt's memory rule, and run one heavy command (test suite, browser, build) at a time.
