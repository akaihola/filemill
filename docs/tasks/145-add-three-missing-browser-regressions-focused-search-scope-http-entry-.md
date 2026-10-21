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

## Regression evidence, 2026-10-21

The new checks use the existing disposable `ui_root` fixture and the real
served UI. No application source change was required. All browser waits
use observable state. Existing API and static tests remain unchanged.

- **Focused search:** `test_content_search_tracks_keyboard_and_pointer_focus`
  checks the focused subtree after ArrowRight, all four matches after
  ArrowLeft, and the sibling subtree after pointer navigation. It opens a
  search result and checks its rendered heading and bold text. Replacing
  the focused path expression in [the search client] with `""` failed:
  expected two results, received four.
- **HTTP order:** `test_http_entry_order_survives_name_and_metadata_sort`
  compares visible labels with the real API response. It checks ascending
  and descending name order, directories first, and both size directions.
  Setting `ordered: false` in [the HTTP adapter] failed: the UI put `2.txt`
  before `10.txt`. A separate mutation forced [the model] to call
  `sortOrder(kids)` for every listing. It failed on the same assertion.
- **CSV identity:** `test_duplicate_csv_rows_have_independent_selection`
  runs with pointer and keyboard input. Four rows have repeated values in
  both columns, including two identical rows. Each input mode selects every
  row and checks one selected element, a distinct selection key, and the
  expected preview headers and values. Replacing `name: labels[i]` with
  `name: record[headers[0]]` in [the CSV adapter] failed both cases:
  expected one selected row, received three.

The first mutation run used another checkout's editable package. It was
stopped and is not regression evidence. The repeat used this worktree's
own environment. All four new cases failed against the three mutations.
After restoring the sources, all four passed in 27.40 seconds. The separate
forced-sort mutation failed in 15.51 seconds. All mutations were restored
before the full server run.

[the search client]: ../../ui/core/search.js
[the HTTP adapter]: ../../ui/adapters/http.js
[the model]: ../../ui/core/model/state.js
[the CSV adapter]: ../../ui/adapters/vfs-csv.js

## Validation

The full server command, `timeout 1800 uv run --project server pytest -q
server/tests`, reached its time limit. It printed 414 passing indicators
and no failures, then exited 124. This is not a passing single suite run.

A fresh `pytest --collect-only -q server/tests` listed 1,252 cases in the
same collection order. Validation continued from case 414, repeating the
boundary case to cover any interrupted teardown. The remaining argument
file contained 839 node IDs. This avoids repeating the first 413 completed
cases and keeps each command within the documented timeout.

The continuation finished with 837 passes and two failures. The offline
miss test did not display its cached root row within five seconds. The
nested ZIP JSON refresh test timed out during the initial page load,
before refresh, at its three-second limit. Both cases passed in isolation
on unchanged main (2 passed in 19.90 seconds), then on this branch
(2 passed in 11.46 seconds). No source or test was changed for those retries.
These failures did not reproduce. The broad run remains recorded as failed.
All 1,252 collected cases completed across the bounded runs; the two
failed cases also have passing isolated results. The four new cases
passed both in their focused run and in the broader run.

Further checks passed:

- Documentation tests and the existing bundled static sorting test:
  28 passed, 76 deselected.
- The existing development static sorting test: 1 passed, 76 deselected.
- `uvx pre-commit run --all-files`: all seven hooks passed.
- `node ui/core/model/test.mjs`: model checks passed.
- Ruff check and format check passed for the changed browser suite.
- `git diff --check` passed.

## Memory report

Each command ran alone under a process-group memory guard. The guard
required 2,048 MiB available to start, with the documented 1,536 MiB
fallback after ten minutes. It monitored memory every second and would
stop the process group below 1,024 MiB or above 512 MiB of swap growth.
All admission waits were zero seconds. No memory limit stopped a command.
The two stopped commands below ended by manual correction and timeout.
All readings are in MiB. Elapsed time includes admission and cleanup.

| Command | Outcome | Available: start → final | Swap: start / growth | Elapsed (s) | Exit |
| --- | --- | --- | --- | --- | --- |
| Wrong editable package | stopped while running | 2639 → 2635 | 2392 / +17 | 39.3 | 143 |
| Three mutations | started at once | 2683 → 2599 | 2408 / -51 | 60.2 | 1 |
| Restored new cases | started at once | 2729 → 2697 | 2356 / -14 | 31.2 | 0 |
| Forced client sort | started at once | 2733 → 2663 | 2342 / -3 | 19.1 | 1 |
| Full server run | stopped while running | 2681 → 2420 | 2339 / +1 | 1801.0 | 124 |
| Collect server cases | started at once | 2354 → 2427 | 2328 / +0 | 7.0 | 0 |
| Server continuation | started at once | 2497 → 2918 | 2328 / +114 | 378.2 | 1 |
| Two cases on main | started at once | 2948 → 2807 | 2455 / +11 | 25.2 | 0 |
| Two cases on branch | started at once | 2954 → 2940 | 2461 / +2 | 14.1 | 0 |
| Docs and bundled sort | started at once | 2931 → 2868 | 2410 / +10 | 22.1 | 0 |
| Development sort | started at once | 2981 → 2853 | 2415 / -23 | 18.1 | 0 |
| Gate and model checks | started at once | 2972 → 2806 | 2381 / -5 | 47.2 | 0 |

Commands, in report order:

- **Wrong editable package:** `timeout 1800 env UV_PROJECT_ENVIRONMENT=<shared-checkout>/.venv uv run --project server --no-sync pytest -q server/tests/test_browser_new_ui.py -k 'tracks_keyboard_and_pointer_focus or http_entry_order or duplicate_csv_rows_have'`
- **Three mutations:** `timeout 1800 uv run --project server pytest -q server/tests/test_browser_new_ui.py -k 'tracks_keyboard_and_pointer_focus or http_entry_order or duplicate_csv_rows_have'`
- **Restored new cases:** `timeout 1800 uv run --project server pytest -q server/tests/test_browser_new_ui.py -k 'tracks_keyboard_and_pointer_focus or http_entry_order or duplicate_csv_rows_have'`
- **Forced client sort:** `timeout 1800 uv run --project server pytest -q server/tests/test_browser_new_ui.py -k http_entry_order`
- **Full server run:** `timeout 1800 uv run --project server pytest -q server/tests`
- **Collect server cases:** `timeout 1800 uv run --project server pytest --collect-only -q server/tests`
- **Server continuation:** `timeout 1800 uv run --project server pytest -q @/tmp/filemill145-remaining.args`
- **Two cases on main:** `timeout 1800 uv run --project server --no-sync pytest -q server/tests/test_browser_new_ui.py::test_uncached_destinations_get_valid_offline_answers 'server/tests/test_browser_new_ui.py::test_json_column_refresh_current_source[edit-True-True]'`
- **Two cases on branch:** `timeout 1800 uv run --project server pytest -q server/tests/test_browser_new_ui.py::test_uncached_destinations_get_valid_offline_answers 'server/tests/test_browser_new_ui.py::test_json_column_refresh_current_source[edit-True-True]'`
- **Docs and bundled sort:** `timeout 1800 uv run --project server pytest -q server/tests/test_docs.py static/tests/test_ui.py -k 'test_docs or test_sort_options' --bundle`
- **Development sort:** `timeout 1800 uv run --project server pytest -q static/tests/test_ui.py -k test_sort_options --dev`
- **Gate and model checks:** `timeout 1800 bash -c 'uvx pre-commit run --all-files && node ui/core/model/test.mjs'`
