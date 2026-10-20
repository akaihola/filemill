---
depends-on: [96]
---

# Reconcile TASKS.md with the code: In Progress and legacy completions

`## In Progress` holds 16 issues that no pacer thread is working on, and
`## Completed / Accepted` holds 109 `[ ]` issues without Hai timestamps. Most of the
latter came from the 2026-09-29 migration "docs(tasks): unify completion and
acceptance", which moved the old `## Completed` section in as "awaiting
acceptance". At least one ("Virtualise column rows") seems never to have been
implemented. Antti cannot review 109 items one by one.

For each issue in those two groups, check the code and history (`git log -S`, the
named files, tests, ADRs):

- In Progress, implemented: move to `## Completed / Accepted` as `[ ]` (tracker
  rules). In Progress, not started: move to `## Ordered backlog`.
- Legacy completed, implemented: leave as is.
- Legacy completed, not implemented or only partly: leave the state alone and list
  it.

Write the findings to this issue's description file: one table row per issue with
its reference, verdict, and evidence (commit hash or file), and at the end the
list of legacy items that are not implemented. Do not accept anything (`[x]` is
Antti's). Change only `TASKS.md` and `docs/tasks/`.

Acceptance: every issue of both groups appears in the table; the moves follow the
tracker rules; the steward can turn the table into one bulk decision line for
Antti.






## Reconciliation, 2026-10-17

Reviewed local code and reachable history at `29e2690b` after [96]'s rewrite.
Commit hashes below are from the rewritten history. This is a repository audit,
not new browser qualification or user acceptance. Evidence comes from current
implementations, existing tests, task histories, ADRs and targeted pickaxe
searches (`previewCache`, `VIRTUAL_ROWS`, `wait_for_timeout`,
`pptx-vanilla-viewer`). A historical passing run is labelled as historical;
current regressions do not erase earlier implemented work.

The starting snapshot has the original **16** In Progress entries plus [93]
and [94], and exactly **109** unchecked legacy completions without Hai
metadata (Hai exposes their missing timestamp as the Unix epoch). The two
recent unchecked completions with metadata, and all accepted entries, are
outside the legacy group. A01–A18 and L001–L109 identify snapshot rows, not new
issue numbers; each `[*]` row includes an identifying prefix of its original summary to identify it
uniquely. `ui/` is the shared frontend symlink described by the architecture
review. No application or architecture behavior changes in this audit.

Disposition: move 13 implemented original entries to Completed / Accepted with
`[ ]`; return three unfinished entries to Ordered backlog, explicitly recording
partial work rather than calling them unstarted. Keep [93]/[94] active because
their task descriptions explicitly reserve completion until blocked CI delivery
checks run. Keep all 109 legacy entries in their existing state. No acceptance
checkbox changes, including existing `[x]` entries.

### In Progress snapshot

| Row | Reference and identifying summary | Verdict / tracker action | Evidence |
| --- | --- | --- | --- |
| A01 | [94] Move the CI workflows to action versions that run on Node.js 24 | Blocked; keep active | `7b6630a1`, `.github/workflows/publish.yml`; Node.js 24 action changes exist. `docs/tasks/94-move-the-ci-workflows-to-action-versions-that-run-on-node-js-24.md` records missing push credentials and the unrun GitHub CI acceptance check. |
| A02 | [93] Make main's CI green again: static bundle test failing since 06792cb | Blocked; keep active | `9e9fe166`, `static/test-model.py::test_preview_threshold_folds_only_below_one_third`; the wait and 60 repeated passes are recorded in the [93] description. Publishing rewritten main and the next main CI check remain blocked. |
| A03 | [*] `.jsonl` files larger than 512 KB aren't previewed or made navigable in a contents co… | Implemented; move to completed | `8dbd28a7`, `ui/adapters/vfs-json.js`; JSONL byte spans defer parsing by row. `docs/adr/0068-large-jsonl-is-indexed-not-parsed.md` and `static/test-ui.py` cover large files and malformed rows. |
| A04 | [*] When all folder columns are collapsed, exiting the preview pane using the arrow left … | Implemented; move to completed | `01f8071f`, `ui/core/nav.js`; `static/test-model.py::test_preview_left_expands_parent_when_all_columns_are_folded` covers this exact state. |
| A05 | [*] Treat `.py.j2` as Python. | Implemented; move to completed | `3a18660c`, `ui/core/syntax.js::hlLang`; `.py.j2` selects Python highlighting. |
| A06 | [*] When returning focus back to the containing folder from the preview pane using the le… | Implemented; move to completed | `847671f6`, `ui/core/nav.js`; `static/test-model.py::test_preview_left_preserves_ancestor_folds` covers leaving preview without refolding ancestors. |
| A07 | [*] Add the `Delete` key as a shortcut to delete the current file or directory. | Implemented; move to completed | `fe2d904c`, `2e9fb1bc`, `ui/core/nav.js`; browser tests cover files, directories, empty selection and editor exclusions. The intermittent preview request after deletion is separately [97]. |
| A08 | [30] Prototype one native shell that hosts the DOM renderer in a WebView and supplies the … | Partial; return to backlog | `f73912b4`, `native/webview/`, `native/test_host.py`; `docs/tasks/30-webview-shell.md` and ADR 0065 record 10 native checks passing and the scrolled-row hit test failing. No host passes the complete UI scenario or qualifies as the smallest passing binary. |
| A09 | [64] Keep subfolder and folded parent widths stable during Up/Down navigation. | Implemented; move to completed | `c95582a2`, `4a9d2d99`, `ui/core/model/folding.js`; `server/tests/test_browser_keyboard.py` checks focused/right-hand widths and rounded fold boundaries. Later [75]/[76]/[81] refine the same policy. |
| A10 | [41] Fix plain-text reStructuredText previews in Source and Rendered modes. | Implemented; move to completed | `9fba9118`, `ui/adapters/app-http.js::PreviewHTTP`, `ui/core/syntax.js`; served RST renders with Docutils and Source uses the RST tokenizer. The later browser-local RST dispatch defect is A8 in `docs/ARCHITECTURE-REVIEW.md`, not evidence that the served-file repair never landed. |
| A11 | [*] Delete `providers/json_provider.py`, `providers/csv_provider.py` and their registrati… | Implemented; move to completed | `44f4241f`, `server/src/filemill/vfs.py`; neither `providers/json_provider.py` nor `providers/csv_provider.py` exists; JSON/CSV are browser adapters. |
| A12 | [*] Default `--bind` in `server/src/filemill/cli.py` to `127.0.0.1`. Document it in `SECU…` | Implemented; move to completed | `server/src/filemill/cli.py`, `server/tests/test_cli.py`, `SECURITY.md`; loopback is the default and explicit binds are tested (`88c597b7`). |
| A13 | [*] Replace every `wait_for_timeout` in `static/*.py` and `server/tests/` with `wait_for_…` | Partial; return to backlog | `static/test-ui.py` and `static/test-url.py` still contain many `wait_for_timeout` calls. Some waits were converted (`041c23be`, `9e9fe166`), but the explicit zero-occurrences criterion is false. |
| A14 | [43] Investigate the 11 server browser failures also reproduced on main. | Implemented investigation; move to completed | `docs/testing/remaining-red-tests.md` and its TSV inventory classify legacy HTMX and mobile restore failures; `7945a0e6`, `e0349caa` repair runner/fixture and shared-UI assertions. Current keyboard tests retain restore coverage. The original 11 names/revision were never recorded in [43], so an exact one-to-one reconstruction is unavailable; no claim that current CI is green. |
| A15 | [*] Clarify the meaning of `[~]` in this file. Review Kandev task sessions to find out wh… | Implemented; move to completed | `00dd2c69`, `TASKS.md` Rules: `[~]` explicitly means actively in progress and completion moves to unchecked Completed / Accepted. |
| A16 | [*] Keep `static/test-e2e.py` as a manual check. Describe when and how to run it in `stat…` | Implemented; move to completed | `6e7ee5be`, `static/FSA-TEST-CHECKLIST.md`; documents when, how, prerequisites, disposable fixtures and expected results. `static/test-e2e.py` has an import-safe main guard and stays manual. |
| A17 | [25] Move `static/test-ui.py`, `test-url.py` and `test-rich.py` under pytest with fixtures… | Partial; return to backlog | `33538e5c`, `conftest.py`, `pytest.ini`; pytest collects all three suites, but `static/test-ui.py::main`, `test-url.py::main` and `test-rich.py::main` still aggregate sections through wrapper tests. The requested section split and deletion of old scripts were not completed. |
| A18 | [*] `.py` files are not highlighted at all. | Implemented; move to completed | `f05a6f89`, `ui/core/syntax.js`; Python has a registered lexer and `hlLang` selects it. Python source is also covered by `static/test-ui.py` highlighting checks. |

### Legacy Completed / Accepted snapshot

“Implemented” means the requested behavior/change exists, with later policy
changes and known regressions called out where relevant. It does not accept the
work or certify every old test-suite-wide completion criterion today.

| Row | Reference and identifying summary | Verdict | Evidence |
| --- | --- | --- | --- |
| L001 | [65] [*] Bug: PNG and JPEG preview doesn't work reliably. Sometimes the text `No inline pr…` | Implemented; leave unchecked | `a275ab89`, `58d7d2fe`, `ui/adapters/preview-local.js`; images bypass the text ceiling. `server/tests/test_browser_new_ui.py::test_an_image_past_the_text_ceiling_is_previewed` covers PNG/JPEG. |
| L002 | [*] For hierarchical nested view of JSON, don't use the folder icon. Use the JSON icon fo… | Implemented; leave unchecked | `81241e7c`, `a8219c95`, `ui/core/icons.js` and `ui/adapters/vfs-json.js`; JSON files, objects and arrays have distinct icons, with hierarchy assertions in `static/test-ui.py`. |
| L003 | [67] Use the vertical scrollbar to browse large directories instead of pagination. Virtual… | Implemented; leave unchecked | `30cbef21`, `140a7045`, `ui/core/render.js::columnFor`; virtual rows are painted and evicted by visible range. `static/test-model.py::test_scrolled_virtual_rows_are_evicted` and ADR 0068 cover this. |
| L004 | [*] Per recommendation from task dd6897a9-b54e-4ad4-b9b5-b2372292f4b1, remove ?no-columns… | Implemented; leave unchecked | `f79121e6`, `ca94b450`, `server/src/filemill/urls.py`; obsolete helpers and no-columns layout were retired. ADR 0067 records the replacement URL contract. |
| L005 | [68] Fix server test fixture discovery from the repository root and document the working p… | Implemented; leave unchecked | `32107792`, `server/tests/test_pytest_config.py`, root `pytest.ini` and `server/README.md`; root/server invocation discovers the shared fixtures. |
| L006 | [*] Do issues [38], [39], [40] and [42] each currently sit under both Scheduled and In Pr… | Implemented; leave unchecked | `b5c346e4`, `TASKS.md`; [38], [39], [40] and [42] each occur once as issue bullets. Later acceptance of [38]/[39]/[40] is preserved. |
| L007 | [*] Fix the extra mount prefix in rendered `~/...` Markdown links. | Implemented; leave unchecked | `b8e4f7a1`, `ui/core/markdown-links.js`; both rendered and highlighted home-link paths share prefix normalization, with regressions in `server/tests/test_browser_keyboard.py` and `static/test-ui.py`. |
| L008 | [*] Check the two architecture reviews (`docs/2026-09-05-ARCHITECTURE-REVIEW.md` and `doc…` | Implemented; leave unchecked | `d5b0a55e`, `docs/ARCHITECTURE-REVIEW.md`; the two dated reviews were consolidated, removed and replaced by one remediation order. |
| L009 | [*] Implement highlighting of reStructuredText (not actually properly implemented by [50]… | Implemented; leave unchecked | `99335595`, `c88976bf`, `ui/core/syntax.js`; RST tokenizer handles roles and word apostrophes, with linear matching and plain code-block bodies. |
| L010 | [42] Render `~/...` Markdown links relative to the root mount, with `?f`, instead of depre… | Implemented; leave unchecked | `1bf99afa`, `ui/core/markdown-links.js`; home links use root-relative `?f` destinations; `server/tests/test_browser_keyboard.py::test_home_markdown_link_is_root_relative` retains the assertion. |
| L011 | [37] Make the installed PWA show its server-not-running recovery page when opened while th… | Implemented; leave unchecked | `87bc1f5d`, `server/src/filemill/static/sw.js`, `server/tests/test_pwa.py`; offline recovery exists. Architecture A5 separately records cold-cache and document-caching defects; this is implemented with later reliability gaps, not proof that the recovery work never landed. |
| L012 | [69] Show copied paths in the status bar. Repeat `Ctrl+C` within 5 seconds, with no interv… | Implemented; leave unchecked | `45a78db0`, `60b138fe`, `ui/core/nav.js::copyPath`; five-second selection-aware cycle and status feedback; `server/tests/test_browser_keyboard.py::test_copy_rotation_http` tests both files and directories. |
| L013 | [70] In preview focus, ArrowRight folds the leftmost expanded folder column, then enters f… | Implemented; leave unchecked | `355690fa`, `ui/core/nav.js`; `static/test-ui.py::test_preview_arrow_sequence` checks folding, fullscreen entry and exit. |
| L014 | [31] Evaluate AppKit, GTK and WinUI against the WebView prototype. Record the comparison i… | Implemented; leave unchecked | `822a879e`, `docs/adr/0066-native-toolkits.md`; compares AppKit, GTK 4, WinUI 3 and WebView, records unmeasured costs and decides to retain WebView. It does not claim [30] is qualified. |
| L015 | [71] Let reStructuredText paragraphs fill the available preview width, as Markdown paragra… | Implemented; leave unchecked | `613dfecd`, `a6565f3d`, `ui/core/styles.css`; `static/test-rich.py::test_rst_viewport` checks RST paragraph width and heading sizes. |
| L016 | [*] The `Delete` button in the preview pane gives the red error `Delete failed: actions.r…` | Implemented; leave unchecked | `8f95812b`, `ui/core/render.js::deleteEntry`; success feedback replaces the missing `actions.render` callback. FSA/server deletion regressions remain in browser suites. |
| L017 | [72] Make the browser Back button exit mobile fullscreen preview like Exit fullscreen, wit… | Implemented; leave unchecked | `c68b0abb`, `e7eba60d`, `ui/core/render.js`; `static/test-ui.py::test_mobile_fullscreen_back` covers Back restoring the preview without leaving an empty pane. |
| L018 | [*] There's no way to access the file context menu on desktop browsers. On touch devices,… | Implemented; leave unchecked | `df47ce42`, `ui/core/render.js`; row contextmenu and keyboard menu handling, opaque menu styles and Delete action; static FSA and server browser tests exercise deletion. |
| L019 | [*] On a portrait mobile phone, Markdown preview is wider than the screen. Contents overf… | Implemented; leave unchecked | `ff3be044`, `ui/core/styles.css`; portrait rich tables scroll inside the preview; `static/test-rich.py::test_markdown_viewport` covers widths and fullscreen. |
| L020 | [*] Fix all remaining red tests (listed in project memory), including the one-line cause … | Implemented; leave unchecked | `7945a0e6`, `3e2322d0`, `docs/testing/remaining-red-tests.md`; historical 256-failure inventory has dispositions and recorded 761-test combined green run. New failures [97]/[98] and the [94] baseline link failure are later reports, not an assertion that today has zero red tests. |
| L021 | [73] Fix Markdown source highlighting for headings, URLs and links without treating word a… | Implemented; leave unchecked | `98e3a0b0`, `d895d8cf`, `ui/core/markdown-source.js`, `ui/core/markdown-links.js`; token boundaries and clickable links have focused tests in `static/test-ui.py`. |
| L022 | [74] Remember collapsed JSON paths and apply the same collapse pattern to similar objects … | Implemented; leave unchecked | `64891c71`, `7f56c892`, `ui/core/model/json-collapse.js`; depth-indexed collapse patterns and per-node memory are consumed by JSON previews; model and browser assertions cover reuse. |
| L023 | [*] In hierarchical navigation of `.json`, `.jsonl`, and SQLite `.db` files, when the key… | Implemented; leave unchecked | `75e7910c`, `80c086c3`, `ui/adapters/vfs-json.js`; selected scalars use their own value including empty keys and multiline strings; `static/test-model.py::test_selected_scalar_preview` covers the source variants. |
| L024 | [*] Bug: The `Fullscreen` button causes a full screen view of the file to briefly flash, … | Implemented; leave unchecked | `5af93c28`, `ui/core/render.js`; native fullscreen/fallback state survives redraw. Browser tests check native toggling and denied-request fallback. |
| L025 | [*] When navigating to the parent directory using the left arrow key, make sure the highl… | Implemented; leave unchecked | `94cf5a70`, `59c2334b`, `ui/core/layout.js::revealRow`; `static/test-model.py::test_left_arrow_reveals_selection` covers ordinary and virtual directories. |
| L026 | [75] Use stable folder widths in em units and let previews fill the remaining space. Tune … | Implemented; leave unchecked | `fe3a2306`, `bc606d4e`, `ui/core/model/folding.js`; em-based responsive folder widths and preview threshold tests live in `static/test-model.py`. ADR 0075 later adds widened stops. |
| L027 | [*] Bug: Arrow Right into the preview pane works inconasistently. Sometimes it focuses th… | Implemented; leave unchecked | `9f773f0c`, `ui/core/nav.js`; entering preview preserves layout; `server/tests/test_browser_keyboard.py::test_arrowright_preview_preserves_layout` fixes the previous inconsistent full-width entry. |
| L028 | [76] Keep the focused folder column's width stable during Up/Down navigation, without part… | Implemented; leave unchecked | `fe3a2306`, `ui/core/model/folding.js`; `test_vertical_navigation_keeps_focused_column_whole` and rounded/full-boundary checks in `server/tests/test_browser_keyboard.py` cover stable widths. |
| L029 | [*] Feature: Clicking on a content search result now opens the raw file. Open the rendere… | Implemented; leave unchecked | `87b05682`, `b1d06851`, `ui/core/search.js`; results enter shared navigation and reset an inherited raw view to rendered preview. |
| L030 | [29] Make `ui/core/` a model package with no DOM: nodes, selection, folding arithmetic, ke… | Implemented; leave unchecked | `c0a924ec`, `ui/core/model/`, `ui/core/dom-renderer.js`; `ui/core/model/test.mjs` imports the model without a DOM and audits dependencies. The task description explicitly narrows the boundary: sibling effect/render modules remain DOM-coupled. Missing preview cache is separate [21]. |
| L031 | [*] Delete `_document_page` — document representations, including `layout=no-columns`, no… | Implemented; leave unchecked | `73bee073`, `server/src/filemill/app.py::resource`; `_document_page` is absent and non-raw resources return the client shell. Legacy no-columns was later retired by ADR 0067. |
| L032 | [13] Correct the stale claims that review finding 15 lists in `server/README.md`, `server/…` | Implemented; leave unchecked | `e48c2644`, `docs/tasks/13-correct-stale-documents.md`; the named historical HTMX, tracker and test-count claims were corrected. Later stale renderer claims are separately A11 in `docs/ARCHITECTURE-REVIEW.md`; historical completion is not a current-doc clean bill. |
| L033 | [*] Split `applyScroll` in `ui/core/layout.js` into `foldFromScroll`, `applyWidths`, `pan…` | Implemented; leave unchecked | `ui/core/layout.js::applyScroll` calls `foldFromScroll`, `applyWidths`, `panFocus`, `slideTail`; all four helpers exist and each is under 25 lines. Later dial changes enlarged the coordinator. |
| L034 | [15] Split the decisions table in `static/AGENTS.md` into one dated ADR file per decision … | Implemented; leave unchecked | `docs/adr/0001-one-finder.md` through the extracted dated decision records; `static/AGENTS.md` links the ADR directory instead of keeping the decisions table. |
| L035 | [10] Toggling `Source` / `Rendered` reloads the whole page and causes an uncomfortable bli… | Implemented; leave unchecked | `5a661e00`, `ui/core/render.js`; Source/Rendered updates view state and router history within the existing page; server toolbar/navigation browser tests cover both views. |
| L036 | [*] Delete the `/raw?path=` route in `app.py`. The client builds `${API}/raw?p=` URLs for… | Implemented; leave unchecked | `3b5cc488`, `server/src/filemill/app.py`; only canonical `/api/raw?p=` remains and no `/raw?path=` implementation is present. |
| L037 | [*] Virtualise column rows. `content-visibility` made layout cheap, but a 100 k-entry dir… | Implemented; leave unchecked | `30cbef21`, `140a7045`, `ui/core/render.js`; this formerly conditional task is now implemented by [67], including eviction rather than retaining every row visited. |
| L038 | [6] Centralize file-kind classification across filesystem producers and preview/edit cons… | Implemented; leave unchecked | `883fdee6`, `server/src/filemill/vfs.py::classify_path`, `ui/core/file-kind.js`; language-specific classification tables are exercised by `server/tests/test_file_kind.py` and `static/test-ui.py`. |
| L039 | [44] Document demo instances matching each browser test setup. | Partial; dashboard integration unverified | `df007a91`, `server/README.md` Manual browser test instances; separate fixture roots and ports are documented. No development-dashboard link/configuration is tracked here, so that requested integration cannot be verified from this repository. |
| L040 | [*] Delete `/open-link` and `_parse_desktop_url` in `app.py`. `desktopCard` in `ui/adapte…` | Implemented; leave unchecked | `server/src/filemill/app.py` has neither `/open-link` nor `_parse_desktop_url`; `ui/core/renderers.js::desktopCard` supplies the shared replacement (moved from preview-local). |
| L041 | [*] Give each magic number in `ui/core/state.js`, `layout.js`, `nav.js`, `render.js` a na… | Partial; unnamed constants remain | `ui/core/nav.js` names status/scroll timings, but `ui/core/layout.js` still repeats literal `0.5` thresholds and `ui/core/render.js` uses literal `10` row overscan. The requirement to name and explain every magic number is not met. |
| L042 | [21] Cache the preview element keyed on the previewed node and its `meta`, the same way `c…` | Not implemented; preview cache absent | `ui/core/render.js::renderPreview` creates a new div and revokes previews on every non-editor render; `fillPreview` calls `PREVIEW.render`. No previewCache exists. Architecture A9 and `docs/tasks/29-core-without-dom.md` independently record the missing resize cache. |
| L043 | [*] Delete `/sse/reload` and `LIVE_MODE` in `app.py`, `LIVE_RELOAD_JS` in `styles.py` and… | Implemented; leave unchecked | `server/src/filemill/app.py`, `server/pyproject.toml`; no SSE route, LIVE_MODE, styles module, LIVE_RELOAD_JS or watchfiles dependency remains. CLI live behavior uses the retained explicit reload option. |
| L044 | [*] Run the static and server browser tests through one root `conftest.py` and one Playwr… | Partial; separate browser lifecycles remain | `conftest.py` owns shared fixtures and the CDN proxy is gone, but `server/tests/test_browser_keyboard.py::_ui_page` still starts sync_playwright directly and `server/tests/test_browser_new_ui.py` has its own module Playwright fixture. The requested one-fixture consolidation is incomplete; static section splitting is separately [25]. |
| L045 | [*] Add a preview for `.mp4` files with a `<video controls>` element, as one registry ent… | Implemented; leave unchecked | `ui/core/renderers.js` video registry entry emits `<video controls>`; `server/tests/test_browser_new_ui.py::test_mp4_preview_uses_a_video_control` covers it. |
| L046 | [*] Implement CSV as a browser virtual filesystem in `ui/adapters/vfs-csv.js`, like JSONL… | Implemented; leave unchecked | `b82a09eb`, `ui/adapters/vfs-csv.js`; browser CSV rows expose records and previews without a Python CSV provider. Later unique-label repair is [61]. |
| L047 | [*] Compute the symlink zone map one time per request in `paths.py`. Delete the three oth… | Implemented; leave unchecked | `server/src/filemill/app.py::_zones` caches the map on request.state and passes it to path helpers; `server/src/filemill/paths.py` accepts the shared zones. No duplicate root walks remain in app routing. |
| L048 | [*] Stop `server/tests/conftest.py` from changing the module global `ROOT`. Done when `uv…` | Partial; parallel qualification unverified | `conftest.py` fixtures patch app.state.root, not module ROOT; old server conftest is gone. However the explicit root pytest -n auto acceptance run has no recorded passing evidence, pytest-xdist is absent from declared dev dependencies, and later baseline failures are recorded in [93]/[94]. ROOT cleanup is implemented; parallel qualification remains unverified. |
| L049 | [*] Replace `python-fasthtml` with `starlette` and `uvicorn`. The shell becomes one strin… | Implemented; leave unchecked | `server/pyproject.toml` uses starlette, uvicorn and typer, and `server/src/filemill/app.py` builds the shared shell without python-fasthtml. python-pptx was subsequently removed from runtime intentionally when browser PPTX replaced it; it remains a fixture dependency. |
| L050 | [*] On mobile, long-pressing a file or directory should open a menu of actions to copy it… | Implemented; leave unchecked | `ui/core/render.js` long-press menu and `ui/core/nav.js::copyPath`; `server/tests/test_browser_keyboard.py::test_mobile_long_press_menu_copies_paths_for_files_and_directories` checks all three paths. |
| L051 | [*] Delete `server/src/filemill/styles.py`. The shell links `/ui/core/styles.css`, and no… | Partial; HTML-route condition superseded | `server/src/filemill/styles.py` and APP_CSS tests are absent; `server/src/filemill/app.py` serves /ui/core/styles.css. However /api/preview still emits HTML for RST and virtual members, so the literal no-other-HTML-route requirement is superseded by the retained preview architecture ([33]). |
| L052 | [*] Delete `/api/render` in `app.py`, `render_upload` in `api.py` and `ui/adapters/previe…` | Implemented; leave unchecked | `server/src/filemill/app.py` has no `/api/render`; `server/src/filemill/api.py` has no render_upload; preview-upload.js is absent. `ui/adapters/app-http.js` uses PreviewRich for browser-local Markdown/DOCX. |
| L053 | [*] Each row of a JSONL file must be presented exactly like a hierarchical nested view of… | Implemented; leave unchecked | `ui/adapters/vfs-json.js::withVirtual` constructs JSONL rows as JSON value nodes and `withVirtualPreview` renders them through the JSON hierarchy, including nested objects. |
| L054 | [45] Show JSON children beside a foldable preview of the selected value. | Implemented; leave unchecked | `ui/adapters/vfs-json.js`, `ui/core/syntax.js::jsonHTML`; a selected JSON container opens children and previews the selected value with fold controls; scalar follow-up is L023. |
| L055 | [46] Fix ancestor columns unfolding during down-arrow navigation. | Implemented; leave unchecked | `255edad6`, `2dbd8299`, `ui/core/model/folding.js`; server keyboard tests cover unchanged ancestor folds and rounded boundaries while stepping down. |
| L056 | [*] Keyboard navigation using arrows still doesn't animate folding/unfolding/resizing of … | Implemented; leave unchecked | `ui/core/layout.js` dial glide and `ui/core/nav.js` navigation preserve ongoing transitions; `server/tests/test_browser_keyboard.py::test_arrow_navigation_keeps_fold_animation_running` covers it. |
| L057 | [7] Make entry ordering an adapter-owned contract. | Implemented; leave unchecked | `ui/adapters/fsa.js`, `server/src/filemill/api.py`, `ui/core/model/sort.js`; node.ordered preserves adapter order; `b3fc7f53` also fixes descending names within directory/file groups. |
| L058 | [47] Fold folder columns on preview entry and restore the containing column on exit. | Superseded; entry folding intentionally removed | `ui/core/nav.js` deliberately preserves layout when entering preview (`9f773f0c`); `docs/testing/remaining-red-tests.md` explicitly records the removal of foldAll as superseding [47]. Parent restoration is implemented, automatic entry folding is no longer the contract. |
| L059 | [48] Keep ancestor folding unchanged during Up/Down navigation. | Implemented; leave unchecked | `255edad6`, `ui/core/nav.js`, `server/tests/test_browser_keyboard.py::test_vertical_navigation_preserves_folded_ancestor`; stepping selection retains ancestor folds. |
| L060 | [*] Add a PWA manifest and service worker to the static bundle so `static/index.html` ins… | Implemented; leave unchecked | `static/manifest.json`, `static/sw.js`, `static/build-index.py`; the generated bundle registers its manifest/service worker, except for unsupported file:// registration. Existing service-worker limitations remain A5. |
| L061 | [49] Fix content search errors and restrict search to the focused directory tree. | Implemented; leave unchecked | `ui/core/search.js` passes the focused directory prefix to `/api/search`; `server/src/filemill/api.py` bounds result paths and distinguishes ripgrep failures. [60] subsequently changes the timeout. |
| L062 | [*] The `Fullscreen` button in the preview pane doesn't do anything. No errors seen on th… | Implemented; leave unchecked | `ui/core/render.js` fullscreen button handler and fallback; `server/tests/test_browser_new_ui.py::test_preview_fullscreen_control_toggles_and_exits` and denial fallback verify behavior. |
| L063 | [50] Fix missing reStructuredText rendering and highlighting after the initial implementat… | Implemented; leave unchecked | `03965dac`, `ui/adapters/preview-rich.js`, `ui/core/syntax.js`; original RST rendering/highlighting repair landed. Later [41] fixed served RST after the PPTX transition, and architecture A8 still records browser-local dispatch trouble. |
| L064 | [51] Return raw file bytes for URLs without query parameters. | Implemented; leave unchecked | `9ac2ec7a`, `server/src/filemill/app.py::resource`, `server/src/filemill/urls.py`; bare file URLs serve bytes, non-raw query views serve the shell; resource-route tests cover it. |
| L065 | [52] Return focus to the parent column when leaving the preview with ArrowLeft. | Implemented; leave unchecked | `65ef1a75`, `ui/core/nav.js`; leaving preview restores the containing folder; later `847671f6` and `01f8071f` add fold preservation/parent expansion. |
| L066 | [*] Remove every `# noqa: S608` in `server/src/filemill/providers/sqlite.py`. Quote ident… | Implemented; leave unchecked | `server/src/filemill/providers/sqlite.py` quotes identifiers and contains no noqa S608 suppression; SQL identifier tests are in `server/tests/test_providers_sqlite.py`. |
| L067 | [53] Let Markdown paragraphs wrap to the preview width instead of preserving linefeeds. | Implemented; leave unchecked | `ab6c5d05`, `ui/adapters/preview-rich.js`; Markdown soft breaks flow as spaces while explicit hard breaks remain; rich-preview checks cover both. |
| L068 | [*] Typing a right arrow when the rightmost column before the preview is focused should f… | Implemented; leave unchecked | `a614214e`, `ui/core/nav.js`; ArrowRight enters preview, and ArrowUp/Down/PageUp/PageDown scroll its body; server keyboard tests use scrollable preview fixtures. |
| L069 | [*] Delete `static/hotreload.py`, `forgetRoots` in `ui/adapters/storage.js`, and `PYGMENT…` | Implemented; leave unchecked | `6f26dd02`; `static/hotreload.py` and styles.py are absent, and `ui/adapters/storage.js` has no forgetRoots. |
| L070 | [54] Keep all Markdown previews within the portrait screen width. | Implemented; leave unchecked | `4a209673`, `ui/core/styles.css`; portrait code wraps; later `ff3be044` additionally contains wide tables. Static Markdown viewport tests cover both. |
| L071 | [55] Fix the favicon 404 and `renderPage is not a function` error. | Implemented; leave unchecked | `c160a342`, `feb0607c`, `ui/core/deeplink.js`, `server/src/filemill/pwa.py`; deep links use the current render action, favicon route exists and browser checks retain favicon errors. |
| L072 | [*] In `ui/adapters/vfs-json.js`, merge `withJsonl` and `withJson` into `withVirtual`, an… | Implemented; leave unchecked | `ui/adapters/vfs-json.js` exports `withVirtual` and `withVirtualPreview`; the separate withJson/withJsonl wrapper exports are absent. Large JSONL indexing remains inside the shared adapter. |
| L073 | [20] Create `ui/core/limits.js` with one `TEXT_MAX` and one image extension list. Create o… | Implemented; leave unchecked | `ui/core/limits.js`, `ui/core/mount.js`, `ui/core/model/deeplink.js`; shared limits/image list, mountRoot and currentPath exist; pathParts is absent. ADR 0071 intentionally introduces a separate bounded JSON_MAX. |
| L074 | [22] Replace `cursor[i]`, `sel[i]` and `node.lastSel` with one selection model: `sel[i]` i… | Implemented; leave unchecked | `ui/core/model/state.js`, `ui/core/model/selection.js`; selection is stored by name in sel, with row indices derived. No cursor array or node.lastSel remains in current source. |
| L075 | [*] Add root `CONTRIBUTING.md` (setup, tests, commit style, STE rule), `SECURITY.md` (thr… | Implemented; leave unchecked | `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md` exist and contain the requested contribution/security/history material. Architecture A3/A5 separately correct overstatements in the security prose. |
| L076 | [*] Document the full port contract in `ui/core/ports.js`: `FS.node`, `FS.blob`, `ROUTER.…` | Implemented; leave unchecked | `ui/core/ports.js` documents FS.node/blob/write/remove, ROUTER.write, RouterPath.base and node fields; the optional rawURL contract was subsequently added by [89]. |
| L077 | [*] Delete `server/PLAN-18.md`, `PLAN-19.md`, `PLAN-20-shared-frontend.md` and `server/lm…` | Implemented; leave unchecked | `server/PLAN-18.md`, `server/PLAN-19.md`, `server/PLAN-20-shared-frontend.md` and `server/lmt/` are absent from the tracked tree; current architecture is under `docs/`. |
| L078 | [*] Make root `README.md` the one explanation of the two editions and their ports. `serve…` | Implemented; leave unchecked | `README.md` documents editions and ports; `server/README.md` and `static/AGENTS.md` link back. Later renderer description drift is explicitly architecture A11, not evidence that the consolidation never happened. |
| L079 | [*] Delete `server/.pi/settings.json`, `server/mobile-narrow-preview.png`, `server/.claud…` | Implemented; leave unchecked | `server/.pi/settings.json`, `server/mobile-narrow-preview.png`, `server/.claude/commands/` and `architecture-review-20260904.html` are absent from the tracked tree. |
| L080 | [56] Add a Rendered / highlighted Source toggle beside Raw and Fullscreen. | Implemented; leave unchecked | `ui/core/render.js` creates pv-view, pv-raw and pv-fullscreen; Source uses withHighlighting in `ui/adapters/preview-local.js`. Static/local view consistency was subsequently repaired by [89]. |
| L081 | [*] Add `.pre-commit-config.yaml` with ruff, ruff-format, mypy, deno fmt, deno lint and `…` | Implemented; leave unchecked | `.pre-commit-config.yaml` contains ruff, ruff-format, mypy, Deno fmt/lint and bundle freshness hooks; `docs/tasks/94-move-the-ci-workflows-to-action-versions-that-run-on-node-js-24.md` records recent passes of the individual checks. |
| L082 | [57] Fix portrait horizontal overflow potentially caused by the fold hint. | Implemented; leave unchecked | `ui/core/styles.css` and `ui/core/layout.js` contain preview overflow and fold geometry rules; portrait viewport/folding checks in `static/test-model.py` and `static/test-rich.py` retain coverage. |
| L083 | [*] Feature: ability to delete a file or a directory from the file manager. | Implemented; leave unchecked | `ui/core/render.js::deleteEntry`, `ui/adapters/fsa.js::remove`, `server/src/filemill/api.py::delete_file`; browser/server API tests cover deleting real files, directories and symlinks. [97] is a later request race. |
| L084 | [*] Feature: Syntax highlight Markdown and HTML files in the `?filemill=highlight` view. | Implemented; leave unchecked | `d00c9e9f`, `ui/adapters/preview-local.js::withHighlighting`, `ui/core/markdown-source.js`; Markdown and HTML Source use syntax rendering rather than rich content. |
| L085 | [58] Preserve preview mode in file URLs so Back from Raw restores the finder. | Implemented; leave unchecked | `cc402412`, `ui/adapters/router-path.js`, `ui/adapters/router-hash.js`; view state survives navigation and Raw creates a history entry with the prior preview retained. |
| L086 | [59] Fix the missing-timestamp error for YouTube WebVTT files. | Implemented; leave unchecked | `27780c16`, `15afe903`, `ui/core/renderers.js::vttHTML`, `server/src/filemill/providers/vtt_provider.py`; YouTube header metadata is accepted while malformed preamble/cues still fail. |
| L087 | [*] In an installed PWA, there is no way to get back from raw file view to the file manag… | Implemented; leave unchecked | `22c2e6ed`, `ui/core/render.js`; installed display mode opens Raw within the shell and retains return/navigation controls; URL tests cover raw navigation state. |
| L088 | [60] Fix content searches failing with `Search timed out`. | Implemented; leave unchecked | `3c4f7ec7`, `server/src/filemill/api.py::search_root`; deployed search timeout increased and result errors retained. Architecture A10 separately requires bounding subprocess work and cancellation. |
| L089 | [61] Choose unique CSV row keys and keep duplicate values independently selectable. | Implemented; leave unchecked | `ce59e1c9`, `aad47fe1`, `ui/adapters/vfs-csv.js`; picks a unique complete column or numbered fallback and preserves dot-prefixed labels; static browser checks exercise duplicate values. |
| L090 | [66] Evaluate hybrid Python/Jinja highlighting and report supported alternatives. | Implemented; leave unchecked | `e3143ad5`, `docs/tasks/66-py-j2-highlighting.md`; reports hybrid Python/Jinja limitations and alternatives. Later treating .py.j2 as Python does not claim a hybrid lexer was implemented. |
| L091 | [62] Prevent further left swipes from exposing a margin beside a fullscreen portrait previ… | Implemented; leave unchecked | `edb7dce1`, `5cd1fd81`, `ui/core/nav.js`; fullscreen portrait swipes are consumed without affecting landscape; server mobile fullscreen tests retain coverage. |
| L092 | [*] Add `deno fmt` and `deno lint` for `ui/` (one pinned binary, no Node project). Format… | Implemented; leave unchecked | `75eba831`, `4d35e2ef`, `deno.json`, `.github/workflows/publish.yml`; pinned Deno, formatting and lint are part of the gate without a Node project. |
| L093 | [*] Add `ruff` and `mypy` to the `dev` group in `server/pyproject.toml`. Add `[tool.ruff]…` | Implemented; leave unchecked | `3b9ca9d1`, `0acceac7`, `server/pyproject.toml`; dev ruff/mypy and line-length 88 exist, Ruff formatting was committed and pre-commit runs both. |
| L094 | [63] Add Raw, Source / Rendered and Fullscreen controls to the preview toolbar. | Implemented; leave unchecked | `55350300`, `ui/core/render.js`; toolbar Raw, Source/Rendered and Fullscreen controls have server browser tests; [89] later fixes duplicate raw controls and local mode. |
| L095 | [12] Make `static/test-ui.py` run to its end, then fix the three checks that fail: the `.p…` | Implemented; leave unchecked | `d481840b`, `static/test-ui.py`; editor viewport resets to the top, main aggregates failures and pytest invokes the suite; historical remaining-red inventory records the later runner corrections. |
| L096 | [*] In `ui/core/state.js`, replace `node.jsonl ? kids : sortKids(kids)` with a `node.orde…` | Implemented; leave unchecked | `06d6e37a`, `ui/core/model/state.js`, `ui/core/model/sort.js`; node.ordered controls sorting for virtual providers; server SQLite listings carry ordered records and HTTP preserves the flag. |
| L097 | [28] Grow the editor behind the `FS.write` port: undo, find, a line gutter and a "modified… | Implemented; leave unchecked | `ui/editor/undo.js`, `find.js`, `gutter.js`, `modified.js`, `editor.js`; `static/test-ui.py::editor_feature_checks` exercises each feature behind FS.write. |
| L098 | [27] Try reStructuredText rendering in the browser with Pyodide or a WASM tool, behind the… | Implemented; leave unchecked | `7c98b7be`, `docs/adr/0064-rst-browser-evaluation.md`, `static/measure-rst.py`; real-runtime sizes, cold/warm times, consent, concurrent-source isolation and parser safety are documented. |
| L099 | [*] Render `.pptx` in the browser: unzip the file and show the slide text, as one registr… | Partial; preview API deletion superseded | `ui/adapters/preview-rich.js::pptxHTML` extracts ZIP/XML slide text; Python PPTX renderer/runtime dependency are gone. However `/api/preview` still exists for RST and archive members in `server/src/filemill/app.py`; the task literal delete-all-preview-API goal is no longer satisfied. |
| L100 | [24] Reduce `app.py` to routing: move `_resolve_safe` and the symlink map to `paths.py` an… | Partial at audit; leave unchecked | `server/src/filemill/paths.py`, `pwa.py`, `app.py`; containment/mount helpers and PWA routes moved to dedicated modules but the [archive provider] still had two local `zstandard` imports (`97ca55f1`, 2026-10-07). |
| L101 | [33] Keep the URL contract, drop the server-side representations: the server sends bytes f… | Partial; server representations remain | `server/src/filemill/app.py::resource` serves bytes or shell, but `server/src/filemill/preview.py` still contains render_source/_highlight_source and imports Pygments; RST and archive-member representations still use `/api/preview`. The proposed all-client rendering end state is only partly reached. |
| L102 | [35] Decide the fate of the `/w/` named mounts and their CORS middleware: delete them, or … | Implemented; leave unchecked | `docs/tasks/35-decide-web-mounts.md`, `SECURITY.md`, `server/src/filemill/app.py`; explicit decision retains same-origin mounts and removes permissive CORS middleware. Architecture A3 separately notes that no CORS is not write authorization. |
| L103 | [32] Render Markdown and `.docx` in the browser in the server edition too. Serve the pinne… | Implemented; leave unchecked | `ui/vendor/`, `ui/adapters/preview-rich.js`, `ui/adapters/app-http.js`; Markdown/DOCX render in both editions from pinned server-vendored modules, and rendering.py plus Python Markdown/DOCX deps are gone. Later link regressions are separate issues. |
| L104 | [34] Make the SQLite provider return JSON only. The client renders tables and rows with th… | Implemented; leave unchecked | `server/src/filemill/providers/sqlite.py` emits records, not HTML; `ui/adapters/vfs-json.js` renders those records through JSON; `c5e94775` removes orphaned VFS preview helper. |
| L105 | [9] Close the conditional `ViewSpec` proposal: [34] removed the six-argument interface. | Implemented; leave unchecked | `docs/tasks/9-vfs-viewspec.md`, `server/src/filemill/vfs.py`; the conditional ViewSpec proposal is explicitly closed after SQLite JSON-only. No ViewSpec abstraction was introduced. |
| L106 | [26] Create one renderer registry, a list of `{kind, render, fallback}`. Both editions fil… | Implemented; leave unchecked | `ui/core/renderers.js::CORE_RENDERERS`, `addRenderers`, `renderNode`; both app adapters register the shared core plus edition entries, with declared fallbacks. |
| L107 | [36] Decide how the installed PWA gets a running server: a systemd or launchd unit, a laun… | Implemented; leave unchecked | `499222cf`, `docs/tasks/36-pwa-start-server.md`, `ui/adapters/app-http.js`; decision is an explicit server-unavailable/retry page, not an implicit browser process launcher. Offline recovery was added by [37]. |
| L108 | [*] Add a `LICENSE` file with the MIT license text. `README.md` already says MIT. Use the… | Implemented; leave unchecked | `4025d15c`, `LICENSE`; MIT text and Antti Kaihola copyright are present. |
| L109 | [*] Feature: Move to using `pptx-vanilla-viewer` from a CDN for previewing PowerPoint fil… | Superseded; CDN viewer replaced by local text | `ui/adapters/preview-rich.js::pptxHTML` uses local ZIP/XML extraction, not pptx-vanilla-viewer. `docs/testing/remaining-red-tests.md` records replacement of CDN/stub expectations with real offline fixtures. README CDN promises are stale (architecture A11). No current implementation of the requested CDN viewer. |

### Steward decision input

99 legacy entries have implementation evidence; ten need a separate decision
below. The 13 newly moved implemented entries can be reviewed in the same batch.
Suggested bulk decision wording for Antti: “Accept the 99 implemented legacy
rows in [95] and its 13 newly completed rows; leave L039, L041, L042, L044, L048, L051, L058, L099, L101 and L109 pending.” This is a proposal for the steward, not acceptance or
a tracker command. [93], [94], [95], [96] and the recent portability completion
are outside that proposed acceptance set.

The backlog moves retain their dependencies: [30] follows [29], which retains
[21] as a prerequisite; [25] follows [12]. All three returned issues have partial
work and need resumption, not a fresh implementation. The historical [31]
evaluation remains completed even though it evaluated an unqualified prototype;
its evidence explicitly declines a native binary selection.

### Validation

An audit assertion initially failed with `coverage: 0/127 rows` before these
tables existed. After the report and tracker moves, verify 127 unique rows,
original summary prefixes/references and evidence, 109 unchanged legacy states, 13
completion moves, three backlog moves, two preserved blockers, no lost or added
issues and unchanged acceptance for every issue. Compare issue blocks against
`29e2690b:TASKS.md` after removing only checkbox/status and Hai metadata: moved
summaries, dependency bullets and original line wrapping must remain unchanged.
Check backlog dependency order, table file/commit references and `git diff --check`.
Validation results: the audit assertions passed for all 127 rows and all 160
tracker issues. Issue blocks match the starting snapshot byte for byte after
status/metadata removal; Hai added the required `[*]` reference to the formerly
bare manual-test item. Sections occur once in the required order; prerequisites
are preserved. All cited commits resolve, and current evidence files exist;
absent paths are cited only as deletion evidence. `git diff --check` passed.

`uv run --project server pytest server/tests/test_docs.py
server/tests/test_pytest_config.py server/tests/test_file_kind.py -q` passed:
31 tests. `pre-commit run --all-files` passed all six hooks with Python 3.13.
The default Python 3.14 run passed five hooks but mypy could not import
zstandard, which the runtime dependency marker excludes on that Python version.
Python 3.12 was unavailable locally; no 3.12 pass is claimed. The 3.13 gate used
a temporary external virtual environment and changed no dependency files.

Only TASKS.md and this description change. No application tests need new cases
because no application behavior changes; the original missing/incomplete work is
reported, not repaired by this documentation task.

### Legacy items not implemented in full

- **L039 [44], demo instances:** commands and separate ports exist; requested
  development-dashboard links cannot be verified in this repository. Steward:
  verify the external dashboard or narrow acceptance to documented instances.
- **L041 [*], name every magic number:** several timings are named, but fold
  epsilons and virtual-row overscan remain unnamed. Steward: accept a narrower
  cleanup or schedule the remaining constants.
- **L042 [21], preview element cache:** absent; resize still rebuilds previews.
  Steward: retain pending and schedule architecture A9's preview identity work.
- **L044 [*], one browser fixture:** shared root fixtures and proxy deletion
  exist, but server suites still own separate Playwright lifecycles. Steward:
  retain the consolidation requirement or accept the current fixture boundary.
- **L048 [*], ROOT fixture cleanup and parallel pytest:** app.state isolation
  exists, but the required root `pytest -n auto` pass is not established and
  pytest-xdist is not a declared dependency. Steward: verify parallel execution
  after current baseline failures are resolved, or accept the isolation cleanup.
- **L051 [*], styles.py and no other HTML routes:** styles.py is deleted; the
  retained preview API still sends HTML. Steward: accept the stylesheet cleanup
  with the same server-preview exception as [33].
- **L058 [47], fold on preview entry:** intentionally superseded by preserving
  layout on entry. Parent restoration exists. Steward: retire the old folding
  requirement explicitly rather than asking for a regression to it.
- **L099 [*], browser PPTX plus delete /api/preview:** browser extraction exists;
  the API is retained for RST/archive members. Steward: accept the delivered
  PPTX work with the API exception, or move the API removal to future A8 work.
- **L101 [33], remove server representations:** byte/shell resource routing is
  implemented, but Pygments helpers and the preview API remain. Steward: retain
  the unfinished removal scope alongside architecture A8.
- **L109 [*], CDN pptx-vanilla-viewer:** replaced by offline ZIP/XML slide-text
  previews, without the requested viewer. Steward: explicitly accept the local
  alternative or reopen the viewer requirement; correct the stale README claim
  through A11 in separate work.


### Correction, 2026-10-20

The audit missed existing imports. Both now use a module-level version guard.

[archive provider]: ../../server/src/filemill/providers/archive.py
