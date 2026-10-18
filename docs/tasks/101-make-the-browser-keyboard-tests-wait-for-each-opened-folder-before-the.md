# Make the browser keyboard tests wait for each opened folder before the next key

Steward issue, 2026-10-18. Goal: agentic-leverage (filemill is a tier-1
project in `<steward-vault>/Goals.md`). The roadmap's Phase 0
wants both suites green on `main`, and a red run holds back acceptance of
everything else.

[100] found `server/tests/test_browser_keyboard.py::test_vertical_navigation_preserves_folded_ancestor`
timing out under suite load, at `focusCol === 1 && path.length >= 2`, while
it passed five isolated reruns in 2.25–2.61 s. It presses ArrowRight before
the folder opened by ArrowDown has loaded. [99]'s `88766300` added that wait
to the sibling `test_arrow_navigation_keeps_fold_animation_running`, but not
to this test. Other browser tests may share the pattern.

## Work

1. Reproduce under load, the way [100] did: run the server suite with the
   two static suites in parallel, and note which browser tests time out.
2. Audit every browser test under `server/tests/` and `static/tests/` that
   presses a key depending on a folder, column or preview that an earlier
   key started loading, without waiting for it. List each test with its
   verdict in this file.
3. Add the missing waits the way `88766300` did, in test code only. If a
   test shows the UI itself dropping or misapplying a key, that is a
   product finding: report it with its evidence and leave the test as it
   is.
4. Validate: each changed test passes five isolated reruns, and the full
   server suite passes twice in a row on the branch, with `--durations=20`.

## Ground rules

- Change only tests under `server/tests/` and `static/tests/`, this
  description file and the issue's tracker moves. No product code.
- Follow `AGENTS.md`: red-green, so record the failing run under load
  before the fix.
- Don't push, deploy or restart services.

## Acceptance

- The audit list is here, and every test it marks as racing waits for the
  state it needs.
- Two consecutive full server-suite passes, recorded in a
  `## Result, YYYY-MM-DD` section with their commands and timings.

## Implementation plan, 2026-10-18

1. Move [101] to In Progress with hai-tasks.
2. Run server, static bundle and static development suites concurrently before
   changing tests. Record failures and elapsed times below.
3. Add local readiness waits only where the next key needs a newly opened
   folder. Keep assertions and deliberate rapid-input scenarios intact.
4. Run every changed test in five fresh pytest invocations, including both
   static modes, then run the full server suite twice consecutively.
5. Record results and move [101] to Completed / Accepted with `[ ]`.

Read the architecture review before the audit. Observable-state waits follow
its existing browser-testing guidance and require no architecture changes.
The issue's explicit file scope leaves the architecture review unchanged.

## Keyboard audit, 2026-10-18

Inspected every Python test under both test directories, including keyboard
helpers, synthetic key events, typing and benchmark loops. The tables list
every test with keyboard input. Tests without keyboard input have no
key-after-loading sequence. Parameterized cases share the listed verdict.

"Missing" identifies setup races to fix here. "Ready" means the required
folder, selection, preview or dial state already has an observable wait,
an awaited navigation helper or a locator that waits for the needed row.
"Independent" means the next key uses an already loaded column or tests
editor, menu, clipboard, fullscreen or rapid-input behavior; it does not
need the preceding key's folder read. No timing sleeps are added.

### `server/tests/test_browser_keyboard.py`

| Test | Verdict |
| --- | --- |
| `test_arrow_left_keeps_browser_url_in_sync` | Ready; existing state/content waits cover dependent navigation. |
| `test_parent_column_survives_preview_after_arrowleft_arrowright_cycle` | Ready; existing state/content waits cover dependent navigation. |
| `test_arrowright_preview_preserves_layout` | Ready; existing state/content waits cover dependent navigation. |
| `test_vertical_navigation_preserves_folded_ancestor` | Missing waits: Down opens column 1; first Right opens column 2. Await loaded children and cached rows before entering each. |
| `test_vertical_navigation_keeps_focused_column_whole` | Ready; existing state/content waits cover dependent navigation. |
| `test_vertical_navigation_preserves_rounded_fold_boundary` | Ready; existing state/content waits cover dependent navigation. |
| `test_vertical_navigation_preserves_full_fold_with_equal_widths` | Ready; existing state/content waits cover dependent navigation. |
| `test_arrow_navigation_keeps_fold_animation_running` | Ready; existing state/content waits cover dependent navigation. |
| `test_mobile_long_press_menu_dismissal_preserves_taps` | Independent; no key depends on an unfinished folder read. |
| `test_copy_rotation_http` | Independent; no key depends on an unfinished folder read. |

### `server/tests/test_browser_new_ui.py`

| Test | Verdict |
| --- | --- |
| `test_the_keyboard_model_is_the_shared_one` | Ready; existing state/content waits cover dependent navigation. |
| `test_markdown_rendered_source_toggle_preserves_navigation` | Independent; no key depends on an unfinished folder read. |
| `test_content_search_opens_a_matching_file` | Ready; existing state/content waits cover dependent navigation. |
| `test_large_directory_scrolls_in_one_column` | Ready; existing state/content waits cover dependent navigation. |
| `test_arrow_left_unfolds_each_focused_ancestor` | Ready; existing state/content waits cover dependent navigation. |
| `test_preview_arrow_folds_then_fullscreen` | Ready; existing state/content waits cover dependent navigation. |
| `test_preview_arrow_exits_button_fullscreen` | Ready; existing state/content waits cover dependent navigation. |
| `test_preview_arrow_focus_survives_resize` | Ready; existing state/content waits cover dependent navigation. |
| `test_preview_arrow_rapid_and_editable` | Independent; deliberate rapid fold input on an already rendered preview. Preserve the sequence. |
| `test_preview_arrows_preserve_layout_then_restore_document_parent` | Ready; existing state/content waits cover dependent navigation. |
| `test_arrow_right_from_a_widened_stop_steps_back_to_natural` | Ready; existing state/content waits cover dependent navigation. |
| `test_stepping_over_sibling_folders_rewrites_history` | Ready; existing state/content waits cover dependent navigation. |
| `test_alt_arrows_are_left_to_the_browser` | Independent; no key depends on an unfinished folder read. |
| `test_arrow_navigation_folds_but_never_unfolds` | Ready; existing state/content waits cover dependent navigation. |
| `test_local_rendered_source_round_trip` | Independent; no key depends on an unfinished folder read. |
| `test_editor_features_and_failed_save` | Independent; no key depends on an unfinished folder read. |
| `test_editor_late_write_does_not_touch_next_file` | Independent; no key depends on an unfinished folder read. |
| `test_editor_normalizes_newlines_and_undoes_replacements_and_composition` | Independent; no key depends on an unfinished folder read. |
| `test_editor_find_reveals_long_lines_and_keeps_composition_input` | Independent; no key depends on an unfinished folder read. |
| `test_responsive_widths_survive_keyboard_and_mouse` | Independent; no key depends on an unfinished folder read. |
| `test_selected_scalar_preview` | Ready; existing state/content waits cover dependent navigation. |
| `test_markdown_highlight_links_preserve_source_and_navigation` | Independent; no key depends on an unfinished folder read. |
| `test_context_menu_desktop_and_keyboard` | Independent; no key depends on an unfinished folder read. |
| `test_preview_delete_cancel_confirm_and_keyboard` | Independent; no key depends on an unfinished folder read. |
| `test_delete_key_deletes_selected_files_and_directories_but_not_editors` | Independent; no key depends on an unfinished folder read. |
| `test_delete_waits_for_active_preview_reads` | Independent; no key depends on an unfinished folder read. |
| `test_context_menu_delete_during_navigation` | Independent; no key depends on an unfinished folder read. |
| `test_context_menu_delete_stays_disabled_after_reload` | Independent; no key depends on an unfinished folder read. |
| `test_context_menu_preserves_keyboard_refresh` | Independent; no key depends on an unfinished folder read. |
| `test_markdown_task_checkboxes_toggle_the_source` | Independent; no key depends on an unfinished folder read. |
| `test_markdown_headings_open_as_columns_in_the_server_build` | Ready; existing state/content waits cover dependent navigation. |
| `test_rst_sections_render_through_the_server_in_the_server_build` | Ready; existing state/content waits cover dependent navigation. |
| `test_left_return_ignores_preview_heading_names` | Ready; existing state/content waits cover dependent navigation. |

### `static/tests/test_doc_sections.py`

| Test | Verdict |
| --- | --- |
| `test_markdown_headings_open_as_columns` | Ready; existing state/content waits cover dependent navigation. |
| `test_left_return_ignores_preview_heading_names` | Ready; existing state/content waits cover dependent navigation. |

### `static/tests/test_json_collapse.py`

| Test | Verdict |
| --- | --- |
| `test_json_collapse_paths` | Independent; no key depends on an unfinished folder read. |
| `test_json_array_paths_and_root_fold` | Independent; no key depends on an unfinished folder read. |

### `static/tests/test_model.py`

| Test | Verdict |
| --- | --- |
| `test_model_renderer_selection` | Missing wait: path length can precede folder rows. Await column 1 children and cached rows before Right. |
| `test_preview_left_preserves_ancestor_folds` | Missing waits: each Down/Right setup step must await the next folder rows; selection length alone is insufficient. |
| `test_preview_left_expands_parent_when_all_columns_are_folded` | Missing waits: same nested-folder setup as the sibling fold test. |
| `test_loading_and_navigation_keep_columns_whole` | Missing waits: await a and b rows before entering them. Preserve the deliberate blocked c read and spinner assertion. |
| `test_preview_threshold_folds_only_below_one_third` | Missing waits: replace the uninterrupted Down/Right/Right setup with folder-readiness waits. |
| `test_geometry_changes_preserve_preview_rules` | Ready; existing state/content waits cover dependent navigation. |
| `test_left_arrow_reveals_selection` | Missing wait for directory cases: Home/End selection precedes folder rows. File cases need no folder wait. |
| `test_selected_scalar_preview` | Ready; existing state/content waits cover dependent navigation. |

### `static/tests/test_preview_views.py`

| Test | Verdict |
| --- | --- |
| `test_static_rendered_source_round_trip` | Independent; no key depends on an unfinished folder read. |

### `static/tests/test_rich.py`

| Test | Verdict |
| --- | --- |
| `test_markdown_viewport` | Ready; existing state/content waits cover dependent navigation. |
| `test_rst_viewport` | Ready; existing state/content waits cover dependent navigation. |

### `static/tests/test_ui.py`

| Test | Verdict |
| --- | --- |
| `test_context_menu_delete_fsa` | Independent; no key depends on an unfinished folder read. |
| `test_preview_arrow_sequence` | Ready; existing state/content waits cover dependent navigation. |
| `test_copy_interaction_reset` | Independent; no key depends on an unfinished folder read. |
| `test_copy_refusal_fallback` | Independent; no key depends on an unfinished folder read. |
| `test_copy_pending_reset_and_missing_clipboard` | Independent; no key depends on an unfinished folder read. |
| `test_copy_preserves_native_text_copy` | Independent; no key depends on an unfinished folder read. |
| `test_copy_late_completion_does_not_replace_new_cycle` | Independent; no key depends on an unfinished folder read. |
| `test_copy_status_click_after_refused_rotation` | Independent; no key depends on an unfinished folder read. |
| `test_directory_states` | Ready; existing state/content waits cover dependent navigation. |
| `test_keyboard_vertical` | Ready; existing state/content waits cover dependent navigation. |
| `test_keyboard_horizontal` | Missing wait: first Right opens alpha; await its rows before the next Right. Later loop iterations must await the next column, not only the focused one. |
| `test_folding_dial` | Missing waits: initial Right loop checks focus only. Await the next folder rows before each Right; preserve later geometry checks. |
| `test_preview` | Independent; no key depends on an unfinished folder read. |
| `test_edit_mode` | Independent; no key depends on an unfinished folder read. |
| `test_auto_preview` | Ready; existing state/content waits cover dependent navigation. |
| `test_settings` | Independent; no key depends on an unfinished folder read. |
| `test_typeahead` | Independent; no key depends on an unfinished folder read. |
| `test_copy_path` | Independent; no key depends on an unfinished folder read. |
| `test_refresh` | Ready; existing state/content waits cover dependent navigation. |
| `test_sort_options` | Ready; existing state/content waits cover dependent navigation. |
| `test_render_cost` | Independent; deliberate rapid benchmark keys in loaded columns. Existing row-cache waits guard entry. |

### `static/tests/test_url.py`

| Test | Verdict |
| --- | --- |
| `test_fullscreen_survives_resize` | Independent; no key depends on an unfinished folder read. |
| `test_history_replacement` | Ready; existing state/content waits cover dependent navigation. |

Audit total: 81 test functions, 9 with missing readiness waits.

## Red evidence, 2026-10-18

Started these unchanged suites concurrently, with output saved separately:

```bash
# from server/
uv run pytest tests --durations=20
# from the repository root, in two other processes
uv run --project server pytest static/tests --bundle --durations=20
uv run --project server pytest static/tests --dev --durations=20
```

The named test passed in that run. While all three suites were still running,
a temporary pytest plugin wrapped `_ui_page` and delayed `FS.ensureLoaded`
by 150 ms in the browser with a promise before calling the original loader.
It changed no product files or assertions. This reproduces a folder that has
not opened when the next key arrives, independently of host scheduling.
A first diagnostic using a blocking Python route handler passed in 7.23 s;
that handler also blocked delivery of the next test command, so it did not
exercise the race. The browser-side delay does.

```bash
PYTHONPATH=/tmp uv run --project server pytest server/tests/test_browser_keyboard.py::test_vertical_navigation_preserves_folded_ancestor -p filemill_101_delay -q --tb=short --durations=20
```

Result before the fix: 1 failed in 35.75 s, call 33.34 s, at the original
`focusCol === 1 && path.length >= 2` wait, with a 30000 ms timeout.
The temporary plugin delays only the test page's loader and is not committed.
Its injected wrapper is:

```javascript
const load = FS.ensureLoaded.bind(FS);
FS.ensureLoaded = async node => {
    await new Promise(resolve => setTimeout(resolve, 150));
    return load(node);
};
```

The portability guard also failed before test changes because the newly
added descriptions for [101] and [102] contained a private goals path.
This description now uses a portable placeholder. The identical one-line
correction for [102] requires the requested scope exception.

## Result, 2026-10-18

### Concurrent baseline

The three commands in Red evidence ran concurrently. No browser test timed
out. Results:

| Suite | Result | Pytest elapsed |
| --- | --- | --- |
| Server | 852 passed, 1 failed, 3 warnings | 808.52 s |
| Static bundle | 147 passed, 1 warning | 577.43 s |
| Static development | 147 passed, 1 warning | 606.98 s |

The server failure was the portability guard for [102]'s private goals path.
The separate pre-change guard run failed on both [101] and [102] in 0.69 s.
[101]'s description was corrected within the allowed scope.

### Changes and delayed-read regression

Added readiness waits in all nine tests marked "Missing" in the audit. Each
wait checks loaded children and cached rows for the folder the next key
enters. Existing assertions, deliberate blocked reads and rapid-input
checks are preserved. No product code changed and no additional product
defect was found by this audit.

The exact delayed-read command in Red evidence passed after the fix:
1 passed in 9.86 s, call 7.25 s. Ruff lint, Ruff format and `git diff --check`
passed for the three changed test modules.

### Five isolated reruns per changed test

All 85 fresh pytest invocations passed, including every parameterized case
and both static modes. Each invocation ran one test function:

```bash
uv run --project server pytest <module>::<test> -q --tb=short --durations=20 [--bundle|--dev]
```

The mode argument is omitted for the server test. Module abbreviations in
the table refer to the full paths in the audit headings above. Ranges are
pytest elapsed seconds per invocation, including parameterized cases.

| Module / test | Mode | Runs | Elapsed seconds |
| --- | --- | --- | --- |
| `server/tests/test_browser_keyboard.py::test_vertical_navigation_preserves_folded_ancestor` | server | 5 passed | 4.80-7.97 |
| `static/tests/test_model.py::test_model_renderer_selection` | bundle | 5 passed | 3.00-4.96 |
| `static/tests/test_model.py::test_model_renderer_selection` | dev | 5 passed | 2.87-4.95 |
| `static/tests/test_model.py::test_preview_left_preserves_ancestor_folds` | bundle | 5 passed | 3.41-4.80 |
| `static/tests/test_model.py::test_preview_left_preserves_ancestor_folds` | dev | 5 passed | 3.17-5.53 |
| `static/tests/test_model.py::test_preview_left_expands_parent_when_all_columns_are_folded` | bundle | 5 passed | 3.16-4.41 |
| `static/tests/test_model.py::test_preview_left_expands_parent_when_all_columns_are_folded` | dev | 5 passed | 2.25-3.67 |
| `static/tests/test_model.py::test_loading_and_navigation_keep_columns_whole` | bundle | 5 passed | 2.57-4.08 |
| `static/tests/test_model.py::test_loading_and_navigation_keep_columns_whole` | dev | 5 passed | 2.79-3.98 |
| `static/tests/test_model.py::test_preview_threshold_folds_only_below_one_third` | bundle | 5 passed | 6.73-9.65 |
| `static/tests/test_model.py::test_preview_threshold_folds_only_below_one_third` | dev | 5 passed | 7.06-10.12 |
| `static/tests/test_model.py::test_left_arrow_reveals_selection` | bundle | 5 passed | 13.09-21.15 |
| `static/tests/test_model.py::test_left_arrow_reveals_selection` | dev | 5 passed | 14.26-18.95 |
| `static/tests/test_ui.py::test_keyboard_horizontal` | bundle | 5 passed | 2.09-2.99 |
| `static/tests/test_ui.py::test_keyboard_horizontal` | dev | 5 passed | 2.08-3.95 |
| `static/tests/test_ui.py::test_folding_dial` | bundle | 5 passed | 32.01-33.26 |
| `static/tests/test_ui.py::test_folding_dial` | dev | 5 passed | 32.48-34.50 |

Total: 175 passing parameterized test cases.

### Full server validation and remaining blocker

From `server/`, after the concurrent baseline finished:

```bash
uv run pytest tests --durations=20
```

First validation run: 852 passed, 1 failed, 3 warnings in 531.72 s.
Process wall time was 533.09 s. All browser tests passed. The sole failure
was `tests/test_docs.py::test_documentation_uses_portable_development_examples`,
which reports the private goals path on line 8 of
`docs/tasks/102-audit-the-technical-roadmap-against-main-and-draft-the-next-phase-s-is.md`.

Proposed correction: replace that private path with
`<steward-vault>/Goals.md`, exactly as corrected in [101]. The user was
asked for this scope exception because the ground rules permit only test
files, this description and [101]'s tracker moves. No reply had arrived
when validation finished, so [102]'s description remains unchanged.
The guard itself is unchanged.

Two consecutive full-suite passes have **not** been achieved. The second
run is deferred until the known documentation failure is corrected.
[101] remains In Progress; it is not marked complete or accepted, and the
branch is not merged. No push, deployment or service restart was performed.

Implementation commits: `7a9be163` records the plan and audit; `6eac522b`
adds the readiness waits. The final evidence is committed separately.
