Steward issue, 2026-10-21 17:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 1.5 h.


The steward's browser evidence packet (`<steward-vault>/agents/steward/log/2026-10-21-filemill-browser-evidence.md`, vault [76], "Draft issues" D1–D3) found three behaviours that only API or static checks cover. Each regression must fail on the bug it guards against.

## Work

1. **Focused search scope (D1).** Extend the served browser suite with disposable files: the same marker in the root, a sibling directory and two descendants of the focused directory. Search after both keyboard and pointer focus changes. Only the focused tree's matches appear; changing focus changes the scope; clicking a result opens a rendered preview. The test fails when the client sends the root path instead of the focused path.
2. **HTTP entry order (D2).** With disposable mixed-case folders and numeric-looking names such as `10.txt` and `2.txt`, compare visible row order with the API response. Ascending name sort keeps server order; descending reverses within directories and files while keeping directories first; metadata sorting still works. The test fails if the HTTP adapter drops its ordered flag or the renderer re-sorts the server list.
3. **Duplicate CSV rows (D3).** Extend the CSV browser cases with a file that has no unique column, repeated first-column values and identical rows. Select each row by pointer and keyboard: exactly one row is selected at a time, each has its own selection key, and the preview belongs to that row. The test fails when selection is keyed by the first-column value.

## Acceptance

- Each new test is shown failing against a deliberately broken variant (record how), then passing.
- Existing API scope and static browser tests are kept; waits are state-based.
- `server/tests/test_docs.py` passes.

- Your completion message lists the tests added and the checks run.
- No push, deployment, live service, real account or credential. Memory: follow your launch prompt's memory rule, and run one heavy command (test suite, browser, build) at a time.

## Implementation plan

- Add served browser checks in [the shared UI suite]. Use disposable files.
- Check focused search after keyboard and pointer navigation. Check the
  complete result set and open a rendered result.
- Compare name order with the real directory API. Check both directions
  and file metadata sorting through the settings menu.
- Select duplicate CSV rows by pointer and keyboard. Check one selected
  row, distinct selection keys and the preview values for each row.
- Run each check against a temporary broken variant, restore the source,
  and record the failing assertion. Run the browser and documentation checks.

[the shared UI suite]: ../../server/tests/test_browser_new_ui.py
