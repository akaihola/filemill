# Remaining red tests

## Baseline and execution

This task started from `2163673`, after rebasing onto main on 2026-09-20.
The project memory baseline spans September 15–19. Its counts overlap and
must not be added together. The root-row fix is already present in `055f4f6`.

Before runner repairs:

- `cd server && .venv/bin/python -m pytest tests/test_api.py::test_dir_owns_stable_entry_order -q`
  errors because the server configuration hides the root `client` fixture.
- Root pytest against `static/test-ui.py` fails with
  `asyncio.run() cannot be called from a running event loop`.
- Static suite functions call `sys.exit(0)` on success, which pytest treats as
  a failure. The old CI script commands do not call those functions at all.
- Importing `static/test-e2e.py` launches an interactive browser and waits for
  folder selection and terminal input. It now has a main guard. It remains a
  manual check and is not part of the autonomous suite.
- The browser fixtures require `python-pptx`, now a development dependency.

The full rich suite already calls `rst_checks`; the full UI suite already calls
`editor_feature_checks`. No duplicate tests were added for the old CLI shortcuts.

The first complete execution after runner repairs reported 256 failures and
483 passes in 983.61 seconds. One failure was a temporary fixture-parameter
rename in `test_fullscreen_survives_resize`, corrected before the retry. The
other failures include 178 safety cases blocked by a stale resolver spy and
route tests affected by CLI state leakage. Individual node IDs are recorded in
[the failure inventory](remaining-red-tests.tsv).

## Dispositions

| Failure | Classification and resolution |
| --- | --- |
| Missing server fixtures, nested Playwright event loop, SystemExit | Test execution defects. Use root pytest configuration, separate sync/async fixtures, and aggregated assertions. |
| Deno checks on minified vendor code | Configuration defect. Exclude only `ui/vendor/`; keep first-party checks. |
| Ruff/Deno formatting drift | Format files reported by the existing checks and regenerate the bundle. |
| `api.py` entry_order_key mypy errors | Type inference defect for heterogeneous dictionaries. Cast the known name/bool fields at the sort boundary without changing runtime behavior. |
| `test_dir_owns_stable_entry_order` | Fixture drift. Include every file now supplied by `tmp_root`, preserving the required order. |
| `test_large_directory_is_paginated_in_stable_order`, `test_directory_at_page_limit_keeps_small_response` | Fixture drift. Test an isolated subdirectory with exactly 501 or 500 entries instead of relying on the shared root's file count. |
| `test_html_preview_iframe_uses_the_canonical_file_path` | Broken behavior. `/api/preview` omitted the root-relative URL when dispatching, so nested HTML/PDF/image previews fell back to a basename. Pass the encoded, HTML-escaped canonical URL. |
| `test_shared_ui_explains_unavailable_server` | Obsolete inline-script assumption after ES module extraction. Follow the shell's entry module and assert the served adapter contains the unavailable-server text. |
| Legacy `/f/` navigation and mobile restore tests | Routes were intentionally disabled in `0cae978`. Remove the legacy-query test and its unused HTMX helpers; retain nested navigation coverage and port restore tests to root-relative shared-UI URLs/selectors. Bare file URLs now return bytes, so preview tests explicitly request `filemill=render`. |
| Four focused-preview scroll checks | Invalid fixture: the selected leaf held only one short line. Give it scrollable content so all four directional assertions exercise the intended behavior. |
| Registry kinds assertion | Intentional MP4 renderer addition. Include `video` in the expected registry. |
| `large.png` / `large.jpeg` click timeout | Wrong fixture column: images are in `mixed`, column 1, not its `sub` directory at column 2. Correct the selectors. |
| CSV fallback row names | Fixtures accidentally supplied a valid unique `note` column. Task [61] requires selecting such a column. Use duplicate notes to exercise the intended numbered-row fallback; `data.csv` still covers choosing a later unique column. |
| JSONL row key/value table assertion | Obsolete representation after the JSON hierarchy work. Assert the navigable field names and parsed JSON values, retaining the no-server-preview-request assertion. |
| CLI default-root assertion and subsequent resource-route failures | CLI moved configuration to `app.state.root`; test the current field and restore it and the live-mode environment after each CLI test. |
| 178 path-safety failures | The spy still took two resolver arguments. Forward the optional `zones` argument. All containment and canary assertions remain unchanged. |
| Initial virtual-column blank area | Real behavior regression. Paint the visible range after DOM attachment; new checks cover 20, 999 and 1000 rows plus existing far-row reveal tests. |
| HTML/VTT highlighted source | Real dispatch bug. Selecting PreviewLocal still selected the HTML/VTT renderer. Pass the explicit text kind for source mode, retaining the text size limit. |
| PowerPoint paragraph spacing | Real display bug. Extracted newlines collapsed in HTML paragraphs. Preserve whitespace in slide text. |
| PowerPoint CDN/stub assertions | Obsolete after the local ZIP/XML renderer replaced the CDN viewer. Use a real compressed slide fixture and assert offline rendering without viewer requests. Reject invalid ZIP bytes explicitly instead of reporting an empty presentation. |
| Back loses the previous folder | Real history bug. A loading render wrote the destination before attaching its column. Suppress that intermediate directory URL write. |
| Static hash URL assertions | Task [58] preserves preview mode; expect `v=render`. Exercise same-folder history replacement using file-to-file arrow moves, not moves into directories. |
| Native fullscreen resize race | Wait for native fullscreen entry/exit before continuing the keyboard test. Previously the second Enter could race the first asynchronous browser request. |
| Raw navigation and query persistence assertions | Tasks [51]/[58] intentionally serve bytes for Raw, preserve the previous rendered file for Back, and remove the file view parameter for a directory. Test those contracts with correct containing-column indices. |
| Preview focus fold assertion | Current keyboard contract preserves layout on preview entry. Assert unchanged fold count and restoration of the actual containing column, covered separately by the parent-selection tests. |
| Folder fixture includes short.txt | Update the listing expectation to include the file deliberately added to the shared fixture. |
| Filename-dependent folding precondition | Task [64] made column widths fixed. Deliberately fold two ancestors, navigate to the sibling directory, and assert folding and equal widths are retained. |
| Wide-chain row selector | `:text-is` on the nested label did not match the row. Select its exact `title`, preserving the layout assertions. |
| Restoring a file adds a phantom root history entry | Initial mount rendered an unloaded root and wrote its URL before restoring the deep link. Suppress URL writes until the root listing is loaded. |
| `/n/` ignores highlighted view | The shell always used a default ViewState. Parse its query parameters like the resource route. |
| Home Markdown mount prefix | The selected mount remained in the relative path, duplicating it. Consume that segment and preserve rendered Markdown navigation. |
| Static bundle font 404 | Real bundler bug. The font regex assumed one CSS line and stopped inlining the font after formatting. Accept whitespace before `format`, including a newline. |
| Plain unknown-language assertion | Markdown is now a known language. Use the existing plain `.txt` fixture to retain the fallback assertion. |
| Deep JSON source fallback | Real regression exposed after the earlier aborts were fixed. JSON.stringify can overflow before the renderer fallback runs. Fall back to the original file provider, and escape serializable values when recursive formatting reaches its limit. |
| Folded ancestor clicks in JSON checks | The tests tried to click hidden rows. Unfold the ancestor as a user must, then select the exact row title. |
| Local-file service worker error | Broken behavior: opening the supported static file tried to register a service worker on `file://`. Register only on HTTP(S); keep the no-console-error assertion and PWA packaging checks. |
| Descending name sort | Broken behavior: `node.ordered` bypassed the direction setting. Reverse the adapter order within directories and files, preserving directories first and ascending adapter order. Add model checks. |
| Sort menu references global SORT_KEYS | ES module extraction hid the internal constant. Assert the three actual menu keys directly. |
| Remembered-folder storage checks | Global function replacement stopped affecting module imports. Use a separate localhost test with real OPFS handles and IndexedDB; observe actual writes to retain debounce and restoration coverage. |
| Refresh selection assertions | Directories sort first, so the first remaining row is `sub`; opening `mixed` auto-previews README. Assert those existing contracts while retaining chain coherence checks. |
| Copy-path includes workspace label | Current `currentPath()` returns the mount-relative path. Assert `mixed/note.md` for the status, clipboard and selected fallback text. |
| Refresh navigation references global SPINE | ES module extraction no longer exposes that internal helper. Read the actual CSS `--spine-w` value and retain the geometry assertions. |
| Historical welcome overlay, duplicate bundle declarations, deep-link `renderPage`, desktop/Markdown/HTML/Pygments previews, wheel exclusions and oversized text | Already fixed at the rebased baseline. Verify through the complete static, preview, packaging and browser suites; no new behavior change for these historical failures. |

## Validation

On 2026-09-20, at `b6059f5`:

- Full suite: `timeout 1800 server/.venv/bin/python -m pytest -c pytest.ini --rootdir=. static server/tests -x -q --tb=short` — **746 passed**, no skips, 636.72 s.
- Final collection: **746 tests** (38 static, 708 server). The rich and UI suites include RST and editor checks; storage restoration is a separate collected test.
- `uvx pre-commit run --all-files` — all six hooks passed: Ruff, Ruff format, mypy, Deno format, Deno lint, bundle consistency.
- `deno run --allow-read=ui/core/model ui/core/model/test.mjs` — passed, including descending adapter-order regressions.

The only full-suite warning is Docutils' existing `writer_name` pending
deprecation in `test_dispatch_rst`; it does not fail a gate. The manual picker
E2E script was not run and is not counted as an automated pass.

- Modular static suite: `timeout 1800 uv run --project server python -m pytest -c pytest.ini --rootdir=. static --dev -q --tb=short` — **38 passed**, no skips, 189.70 s.

Collection increased from 739 to 746: three root-row threshold cases, two
additional nested-media cases, two shell view-mode cases and one storage test,
minus the single retired legacy-route test. No skips or xfails were added.

- Documented server invocation, from `server/`: `timeout 1800 uv run pytest --cov=src/filemill --cov-branch --cov-report=term-missing -q --tb=short` — **708 passed**, no skips, **89%** combined statement/branch coverage, 447.91 s. This verifies root-fixture discovery from the documented working directory.

The coverage run also reported three SQLite `ResourceWarning`s during scalar
preview tests, in addition to the Docutils warning. They were not suppressed;
all applicable gates passed. No automated check remains blocked.

The unchanged issue remains In Progress for the later merge workflow. Removing
that one bullet from both tracker versions leaves byte-identical main text.
Browser checks ran sequentially with the installed Nix browser; CI retains its
normal browser installation step.
