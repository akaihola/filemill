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

## Plan, 2026-10-21

1. Add failing provider-render counts for resize, folding and pending reads.
2. Retain one preview pane with explicit node, metadata and view identity.
   Invalidate pending work when selection leaves, including empty selections.
3. Check edits, metadata changes, mode changes and selection changes.
4. Run the model checks, pre-commit gate, both static suites and server suite
   one at a time under the memory guard. Record results before merging.

## Evidence, 2026-10-21

- **Red before the repair:** the new [UI regressions] counted three provider
  renders after resize and layout work, instead of one. Repeated renders also
  replaced a pane while its metadata read was pending.
- **Corrections during implementation:** retaining DOM exposed Left-arrow's
  dependence on losing focus when the pane was replaced. The [model checks]
  caught that regression and a JSON placeholder retained after its content
  became available. Left-arrow now leaves the preview explicitly, and the
  cache distinguishes placeholders from available previews. The old [Markdown
  viewport check] required a replacement after each resize. It now keeps its
  geometry checks and asserts pane identity and one slow initial render.
  A controlled delayed-outline test also caught a second render when a document
  declined its outline after its preview was visible. Content availability now
  supplies the cache distinction, without keying on the document's directory
  flag. A further failing test forced resize during the metadata read after Save; the refill now
  updates its key before that await.
- **Pending revision correction:** a controlled provider test populated a
  revision before its render resolved. A resize then replaced the pending pane.
  Pending fills now hold their incoming revision and publish the completed key
  only if their token still owns the pane. This covers HTTP providers that read
  their revision with the bytes.
- **Server readiness:** the full covered server run stopped after 415 passes
  when Firefox's fresh Markdown preview was still empty at the default
  five-second assertion timeout. The exact case passed in isolation. That
  condition-based assertion now allows 15 seconds for the real renderer,
  as other Markdown readiness checks do. It still requires the same content.
- **Implementation:** retain one pane, with node/root/port identity and a key
  for metadata values, revision, representation and relevant settings. Preserve
  raw URLs and content nodes across resize and folding. Save and Cancel refill
  the pane. Selection changes, including an empty selection, invalidate old
  async fills. The [lifetime decision] records the boundary.
- **Coverage:** provider render counts cover resize, folding, Save, metadata
  mutation/replacement, selection changes and pending fills. [Mode checks]
  count Source/Rendered changes for Markdown and WebVTT. Existing editor and
  performance budgets remain intact.

## Validation, 2026-10-21

- **Static development:** all 184 checks passed on the final code.
- **Static bundle:** all 184 checks passed on the final generated page.
- **Server:** all 1,248 checks passed with branch coverage (93% total coverage).
- **Final gate:** Model checks and all pre-commit checks passed.
- **Integration:** main's intervening changes contain tracker entries and task
  documents only. The rebase preserves the code tested above.

## Memory guard evidence

Run one heavy command at a time. Admit at 2,048 MiB available. Wait at most
10 minutes, then permit the 1,536 MiB fallback. Stop the process group below
1,024 MiB available or above 512 MiB swap growth. Each run has a 30-minute
execution timeout. Runtime excludes the separate admission wait.

The first full development attempt was interrupted to apply repairs.
A later development rerun was stopped by the memory guard. Its replacement
waited 15 seconds for admission and completed with exit code 0. Neither
interrupted run is counted as completed validation.

All memory readings below are MiB. Negative swap growth means swap use fell.
The command column records the exact guarded command, including sequential
format/build/check groups. It contains no command output.

| Run and command | Outcome | Wait s | Available in / out | Swap start / growth | Runtime s | Exit |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| red: `uv run --project server pytest static/tests/test_ui.py --dev -q -k 'preview_reuse or preview_reuses' --maxfail=2` | started at once | 0.0 | 3234 / 3314 | 2115 / +5 | 14.0 | 1 |
| focused: `uv run --project server pytest static/tests/test_ui.py --dev -q -k 'preview_reuse or preview_reuses or editor_features or render_cost'` | started at once | 0.0 | 3348 / 3076 | 2119 / +1 | 52.1 | 1 |
| prepare: `bash -c 'deno fmt ui/core/render.js && uv run --project server ruff format static/tests/test_ui.py static/tests/test_preview_views.py && static/build-index.py'` | started at once | 0.0 | 3285 / 3250 | 2115 / +0 | 1.0 | 0 |
| static-dev: `uv run --project server pytest static/tests --dev -q` | stopped while running | 0.0 | 3272 / 2849 | 2115 / -8 | 346.5 | 2 |
| save-red: `uv run --project server pytest static/tests/test_ui.py --dev -q -k preview_reuses_pending_editor_save` | started at once | 0.0 | 2896 / 3164 | 2107 / +0 | 7.0 | 1 |
| focus-and-save: `uv run --project server pytest static/tests/test_ui.py static/tests/test_model.py --dev -q -k 'preview_reuse or preview_reuses or model_renderer_selection or preview_left or left_arrow_reveals_selection or editor_features or render_cost' -x` | started at once | 0.0 | 3293 / 3098 | 2107 / -1 | 45.1 | 0 |
| gate: `bash -c 'deno fmt ui/core/render.js ui/core/nav.js && uv run --project server ruff format static/tests/test_ui.py static/tests/test_preview_views.py && static/build-index.py && node ui/core/model/test.mjs && uvx pre-commit run --all-files'` | started at once | 0.0 | 2970 / 3211 | 2106 / +0 | 26.1 | 0 |
| static-dev-final: `uv run --project server pytest static/tests --dev -q -x` | started at once | 0.0 | 3246 / 3262 | 2106 / -6 | 181.2 | 1 |
| static-dev-final-2: `bash -c 'deno fmt ui/core/render.js && static/build-index.py && uv run --project server pytest static/tests --dev -q -x'` | started at once | 0.0 | 3282 / 3135 | 2100 / -5 | 236.3 | 1 |
| static-dev-final-3: `uv run --project server pytest static/tests --dev -q -x` | started at once | 0.0 | 3204 / 3114 | 2094 / +74 | 669.4 | 0 |
| static-bundle: `uv run --project server pytest static/tests --bundle -q -x` | started at once | 0.0 | 3224 / 3024 | 2163 / +2 | 290.6 | 1 |
| outline-red: `uv run --project server pytest static/tests/test_ui.py --dev -q -k delayed_outline_declines` | started at once | 0.0 | 3234 / 3370 | 2179 / +2 | 4.0 | 1 |
| outline-and-viewport: `bash -c 'deno fmt ui/core/render.js && uv run --project server ruff format static/tests/test_ui.py static/tests/test_rich.py && static/build-index.py && uv run --project server pytest static/tests/test_ui.py static/tests/test_rich.py --bundle -q -k "preview_reuse or preview_reuses or delayed_outline_declines or markdown_viewport" -x && uv run --project server pytest static/tests/test_ui.py static/tests/test_rich.py --dev -q -k "preview_reuse or preview_reuses or delayed_outline_declines or markdown_viewport" -x'` | started at once | 0.0 | 3339 / 3197 | 2181 / +25 | 60.1 | 0 |
| static-bundle-final: `uv run --project server pytest static/tests --bundle -q -x` | started at once | 0.0 | 3393 / 3241 | 2205 / +12 | 909.1 | 0 |
| server-final: `uv run pytest --cov=src/filemill --cov-branch --cov-report=term-missing -q -x` | started at once | 0.0 | 3162 / 3192 | 2212 / +83 | 1223.9 | 1 |
| firefox-readiness: `uv run pytest tests/test_browser_new_ui.py -q -k 'markdown_heading_fragment_loads_fresh and missing and firefox' -x` | started at once | 0.0 | 2608 / 2522 | 2264 / +25 | 67.4 | 0 |
| pending-revision-red: `uv run --project server pytest static/tests/test_ui.py --dev -q -k pending_provider_that_populates_revision` | started at once | 0.0 | 2663 / 2528 | 2267 / +7 | 25.2 | 1 |
| pending-revision-green: `bash -c 'deno fmt ui/core/render.js && uv run --project server ruff format static/tests/test_ui.py && static/build-index.py && uv run --project server pytest static/tests/test_ui.py static/tests/test_rich.py static/tests/test_preview_views.py --dev -q -k "preview_reuse or preview_reuses or delayed_outline_declines or pending_provider_that_populates_revision or markdown_viewport or mode_changes" -x && uv run --project server pytest static/tests/test_ui.py static/tests/test_rich.py static/tests/test_preview_views.py --bundle -q -k "preview_reuse or preview_reuses or delayed_outline_declines or pending_provider_that_populates_revision or markdown_viewport or mode_changes" -x'` | started at once | 0.0 | 2513 / 2103 | 2274 / -7 | 75.4 | 1 |
| pending-revision-green-2: `bash -c 'deno fmt ui/core/render.js && static/build-index.py && uv run --project server pytest static/tests/test_ui.py static/tests/test_rich.py static/tests/test_preview_views.py --dev -q -k "preview_reuse or preview_reuses or delayed_outline_declines or pending_provider_that_populates_revision or markdown_viewport or mode_changes" -x && uv run --project server pytest static/tests/test_ui.py static/tests/test_rich.py static/tests/test_preview_views.py --bundle -q -k "preview_reuse or preview_reuses or delayed_outline_declines or pending_provider_that_populates_revision or markdown_viewport or mode_changes" -x'` | started at once | 0.0 | 2706 / 2800 | 2221 / -19 | 181.9 | 0 |
| server-final-2: `uv run --project server pytest server/tests --cov=server/src/filemill --cov-branch --cov-report=term-missing -q -x` | started at once | 0.0 | 3024 / 1774 | 2181 / +406 | 1320.8 | 0 |
| static-dev-final-4: `uv run --project server pytest static/tests --dev -q -x` | stopped while running | 40.0 | 3483 / 1355 | 2443 / -23 | 101.3 | 143 |
| static-dev-final-5: `uv run --project server pytest static/tests --dev -q -x` | started at once | 15.0 | 3278 / 2887 | 2418 / -99 | 606.3 | 0 |
| static-bundle-final-2: `uv run --project server pytest static/tests --bundle -q -x` | started at once | 0.0 | 2889 / 3290 | 2319 / -110 | 559.1 | 0 |
| final-gate: `bash -c 'node ui/core/model/test.mjs && uvx pre-commit run --all-files'` | started at once | 0.0 | 3325 / 3261 | 2208 / +0 | 4.0 | 0 |

[UI regressions]: ../../static/tests/test_ui.py
[model checks]: ../../static/tests/test_model.py
[Mode checks]: ../../static/tests/test_preview_views.py
[Markdown viewport check]: ../../static/tests/test_rich.py
[lifetime decision]: ../adr/0020-pvtoken-guards-preview-fills.md
