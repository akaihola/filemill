---
depends-on: [21]
---

# Make ui/core/ a model package with no DOM

## Model boundary

The shared model is in `ui/core/model/`. Both browser editions import it.

- `state.js` owns the plain node chain, selection, focus and display state.
- `selection.js` owns selection truncation and automatic README previews.
- `sort.js` owns comparison rules. Adapters retain node loading and metadata I/O.
- `folding.js` calculates column spans, fold progress, widths and translations
  from numeric dimensions.
- `keyboard.js` maps plain key/context data to actions and row positions.
- `typeahead.js` matches names without row elements.
- `deeplink.js` formats and walks paths and selects history replacement.

`ui/core/dom-renderer.js` owns DOM handles and measurements. The existing
render, layout and navigation modules beside it retain element creation,
event listeners, preview effects and asynchronous rendering coordination.
The model never imports these modules. Router adapters retain URL transport.

Run `node ui/core/model/test.mjs`. CI runs the same checks with Deno. The
script imports every model module without a DOM, audits their imports, and
checks selection, sorting, folding, keyboard and deep-link edge cases.

## Validation

Checked on 2026-09-19 against main at `9a4c3a0`. Later main changes before
rebase only changed task documentation. The tracker remains In Progress until
the merge stage.

Passing checks:

- `node ui/core/model/test.mjs` and
  `deno run --allow-read=ui/core/model ui/core/model/test.mjs`.
- `python3 static/build-index.py --check`.
- `deno lint ui/core ui/adapters ui/editor` and formatting checks for the model
  and changed renderer logic.
- `timeout 1800 uv run --project server pytest -c pytest.ini
  static/test-model.py
  server/tests/test_browser_keyboard.py::test_renderer_uses_model_state`:
  2 passed. The static test with `--dev`: 1 passed.

The full-suite acceptance criterion is blocked by existing failures:

- Root pytest collection executes the manual `static/test-e2e.py` at import.
  Excluding it exposes the shared Playwright fixture error in all three static
  async suites: `asyncio.run() cannot be called from a running event loop`.
  Both bundle and `--dev` pytest runs reproduce it. No fixture changes were
  included in this refactor.
- The non-browser server run completes with 332 passed and 224 failed on both
  the branch and an isolated main snapshot. All 224 failed test IDs match.
  Command: `timeout 1800 uv run --project server pytest -c pytest.ini
  server/tests --ignore=server/tests/test_browser_keyboard.py
  --ignore=server/tests/test_browser_new_ui.py`.
- The static async bodies were also run through a temporary runner with
  `playwright.async_api`, without the sync fixture. Bundle and main each reach
  96 passing assertions and the same five failures before the same `large.png`
  row timeout. The modular UI run reaches the same timeout. The URL suite has
  five failures in the bundle, all present on main; main additionally fails a
  timing ratio check. Modular URL tests have four existing URL/history
  failures. Rich-preview tests stop at the same missing `.preview-error`
  timeout on both builds and main.
- `test_arrow_left_keeps_browser_url_in_sync` fails with the same URL wait on
  main. The existing server UI fixtures also require undeclared `python-pptx`.
  Supplying it temporarily with `uv run --with python-pptx` lets root-listing
  and deep-link smoke tests pass. The folder-click smoke test fails on both
  branch and main. No dependency changes were made.
- `pre-commit` is absent from PATH, so the checks were invoked through
  `uv run --project server --with pre-commit pre-commit run --all-files`.
  Ruff passes. Formatting reports pre-existing code in seven Python files.
  Mypy reports two existing argument-type errors in `server/src/filemill/api.py:173`.
  The full run times out after 180 seconds in Deno formatting of vendor code.
  Whole-UI Deno lint also reports unchanged vendor code. Application-source
  lint and focused model/renderer formatting pass.

Issue [21] is marked completed, but both main and this branch create a fresh
preview on resize. A browser measurement records one `PREVIEW.render` call and
an unchanged selection on each. This refactor preserves that baseline; it does
not implement a second cache fix.

## AI review

The focused model checks pass in Node and Deno. Bundled static and server
browser checks pass, 2 tests total. The modular static check passes, 1 test.
Source lint, focused formatting and bundle consistency checks pass. The review
found no behavior defect introduced by this extraction.

The recorded non-browser server failures were checked against the saved main
run. All 224 failed test IDs match. Main's application and test sources still
match the baseline revision used for those comparisons.

The tracker audit compares every line against main after removing the single
[29] block. The remaining text matches exactly. Issue [29] occurs once, under
In Progress. A whole-tracker uniqueness claim is blocked: [38], [39], [40] and
[42] each occur under both Scheduled and In Progress on main and this branch.
The audit of numbered IDs and repeated issue titles found no other duplicates
across headings. These pre-existing entries are preserved because this task
requires every other issue to keep main's text. Removing them would be
unrelated tracker maintenance.


## User verification

This change adds no new controls. Both editions retain the same file browsing
behavior. The change separates browser rendering from the shared model so that
navigation and layout decisions can be tested without a browser.

1. Refresh the development or public Filemill page. Click a folder, then a file.
   The folder opens a column and the file opens its preview.
2. Select a folder with Up or Down. Focus stays in its parent column. Use Right
   to enter the opened column and Left to return. Repeat with an empty folder.
3. Scroll the column strip horizontally. Older columns fold into narrow spines.
   Click a spine to reopen it. Resize the window and check that selection stays.
4. Change the sort key between name, size and modified. Toggle hidden files.
   The displayed order and visible rows should follow those controls.
5. Open a nested file, copy its address and reload it. The same path should be
   restored. Existing history failures listed above are not fixed by this change.
6. Repeat the folder, keyboard, folding and sort checks in the static edition
   after granting a test folder through its folder picker.

## Deployment

Merged into main with `--no-ff` in `ac44066`. Both worktrees were clean after
the merge. Issue [29] moved unchanged to Completed; removing its block from
the before/after tracker leaves identical text. The four pre-existing
duplicates recorded above remain unchanged.

Restarted `filemill.service` and `filemill-public.service`; both are active.
The development server, public origin and https://filemill.vempai.men/ serve
the merged shell and all nine checked model, renderer and entry assets.
Live Chromium checks passed on all three endpoints for keyboard navigation,
text preview, shared model identity, deep-link state and selection after
resize, using synthetic files without changing served data. The first
Python HTTP request received 403 from the public endpoint; curl asset checks
and Chromium both succeeded.

The focused checks and baseline suite limitations remain as recorded above.
