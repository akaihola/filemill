<!-- HAI156 final start -->
## Outcome, 2026-10-23

All acceptance checks passed on merged main `104a17b82b3cccbc43dc59a984515d1a7d7a8f0c`.
The six documented root shards executed all 1,501 collected cases,
with matching ID multiplicity. The longest guarded root command took 377.7 s;
each finished below the 25-minute target and unchanged 1,800 s bound.
The full static development suite (193), native contracts (20) and native
UI suite (83) also passed. No hardware or display exception remains.

All assertions remain. The complete partition omits no tests. No dependency
was added and no Filemill service was restarted. User acceptance remains
unchecked. The original aggregate command is replaced for evidence by
[the documented sequential shards][final-test-commands].

## Completion tracker blocker

All twelve acceptance recordings passed at the merged commit above. The
prescribed completion command then failed before updating or staging the
tracker: Hai returned status 422, `Invalid workspace: description exceeds
50,000 characters.` The prescribed fallback state query failed with the same
422, so no completion update was retried. The launch instruction requires
stopping and reporting this failure. The tracker was not changed by either
failed command; its last successful state remains In Progress.

Agent-owned follow-up: shorten this description below Hai's limit while
preserving the audit history in a linked companion document, then resume the
prescribed state query and completion workflow. No owner decision is needed.
The implementation, generated bundle, tests and architecture notes are
already merged; the final report and receipt are preserved in a separate
report commit. User acceptance remains unchecked.

2026-10-23, steward: the implementation history of 2026-10-22 and
2026-10-23 moved unchanged to [the work history], which brings this
description below Hai's limit. The completion move follows.

## Final verification on main

The initial clean-main aggregate stopped at 1,800 s with exit 124; cleanup
finished at 1,802.3 s. The complete after-results follow. Guarded wall time
includes evidence recording overhead; pytest time comes from its final
summary. All rows exited 0. [The acceptance receipt][final-receipt] records
the clean checkout, exact commands, lockfile hash and editable Git input.

| Check | Passed cases / result | Pytest s | Guarded wall s |
| --- | ---: | ---: | ---: |
| keyboard | 67 | 322.72 | 326.7 |
| served-ui-early | 157 | 312.58 | 313.7 |
| served-ui-late | 156 | 376.15 | 377.7 |
| server-contracts | 928 | 21.66 | 24.0 |
| static-ui | 83 | 295.35 | 297.5 |
| static-adapters | 110 | 243.51 | 245.3 |
| static-dev | 193 | 575.40 | 577.0 |
| native-build | built | — | 9.0 |
| native-contracts | 20 | 32.59 | 40.0 |
| native-ui | 83 | 478.84 | 487.9 |
| collections | 1,501 IDs equal | — | 8.0 |
| quality | all hooks + model checks | — | 4.0 |

The served halves report complementary deselections. Both commands passed;
the independent collection comparison includes multiplicity and verifies
that the six completed root commands cover the root collection exactly.
The offline-copy case passed in the late shard and earlier after all its
full-module predecessors. The Edit and five original native failures all
passed in the complete final commands. The quality command passed all seven
hooks, explicit Python lint/format checks and the model checks.
The final report and receipt then passed 32 documentation, readiness and
partition checks in 1.67 s; the report-only edit does not change test inputs.

## 40 slowest completed root cases

These are the slowest complete cases across the six final root JUnit files,
including setup and teardown. The per-command logs retain the requested
40 slowest pytest phases. The stopped baseline could not emit that report,
as described in its historical section. Raw artifacts remain in
[the run directory].

| Complete root case | Seconds |
| --- | ---: |
| [static/tests/test_ui.py::test_folding_dial][final-source-1] | 28.70 |
| [server/tests/test_browser_keyboard.py::test_mobile_portrait_wide_folder_tap_keeps_the_touched_row_on_screen][final-source-2] | 15.42 |
| [server/tests/test_browser_keyboard.py::test_mobile_landscape_wide_folder_tap_keeps_the_touched_row_on_screen][final-source-2] | 14.99 |
| [server/tests/test_browser_keyboard.py::test_mobile_landscape_wide_folder_with_small_server_log_pipe][final-source-2] | 14.49 |
| [server/tests/test_browser_new_ui.py::test_fractional_fold_stops_are_native_scrollbar_endpoints\[1500-20.025em\]][final-source-3] | 14.40 |
| [server/tests/test_browser_new_ui.py::test_markdown_heading_fragment_loads_fresh\[work-Work-0-firefox\]][final-source-3] | 13.51 |
| [static/tests/test_ui.py::test_refresh][final-source-1] | 12.55 |
| [server/tests/test_browser_new_ui.py::test_fractional_fold_stops_are_native_scrollbar_endpoints\[414-None\]][final-source-3] | 12.21 |
| [server/tests/test_browser_new_ui.py::test_warm_startup_offline_reuses_marked_copies][final-source-3] | 12.09 |
| [server/tests/test_browser_new_ui.py::test_fractional_fold_stops_are_native_scrollbar_endpoints\[413-None\]][final-source-3] | 11.85 |
| [static/tests/test_ui.py::test_sort_options][final-source-1] | 10.66 |
| [static/tests/test_ui.py::test_jsonl_rows][final-source-1] | 10.13 |
| [static/tests/test_ui.py::test_edit_mode][final-source-1] | 8.69 |
| [static/tests/test_ui.py::test_json_preview][final-source-1] | 8.48 |
| [static/tests/test_ui.py::test_preview][final-source-1] | 8.20 |
| [server/tests/test_browser_new_ui.py::test_markdown_heading_fragment_loads_fresh\[q1-scope-1-Q1: scope-1-firefox\]][final-source-3] | 8.11 |
| [server/tests/test_browser_new_ui.py::test_markdown_heading_fragment_loads_fresh\[missing-None-0-firefox\]][final-source-3] | 7.90 |
| [static/tests/test_ui.py::test_typeahead][final-source-1] | 7.87 |
| [server/tests/test_browser_new_ui.py::test_markdown_heading_fragment_loads_fresh\[%ZZ-None-0-firefox\]][final-source-3] | 7.78 |
| [server/tests/test_browser_new_ui.py::test_markdown_heading_fragment_loads_fresh\[q1%3A-scope-Q1: scope-0-firefox\]][final-source-3] | 7.65 |
| [server/tests/test_browser_new_ui.py::test_markdown_heading_fragment_loads_fresh\[q1-scope-Q1: scope-0-firefox\]][final-source-3] | 7.62 |
| [server/tests/test_browser_new_ui.py::test_server_loss_keeps_the_view_and_explains_it][final-source-3] | 7.62 |
| [static/tests/test_url.py::test_opfs_sort][final-source-4] | 7.20 |
| [server/tests/test_browser_new_ui.py::test_markdown_heading_fragment_loads_fresh\[caf%C3%A9--tea-Caf\\xe9 &amp; tea!-0-firefox\]][final-source-3] | 7.10 |
| [static/tests/test_ui.py::test_render_cost][final-source-1] | 7.03 |
| [server/tests/test_browser_new_ui.py::test_flings_stop_at_each_fold_stop][final-source-3] | 6.96 |
| [server/tests/test_browser_keyboard.py::test_status_bar_items_stay_on_one_line_when_hints_do_not_fit\[viewport0\]][final-source-2] | 6.79 |
| [static/tests/test_ui.py::test_touch_tap_opens_folder_first_time][final-source-1] | 6.70 |
| [server/tests/test_browser_keyboard.py::test_status_bar_items_stay_on_one_line_when_hints_do_not_fit\[viewport1\]][final-source-2] | 6.53 |
| [server/tests/test_browser_keyboard.py::test_status_bar_items_stay_on_one_line_when_hints_do_not_fit\[viewport2\]][final-source-2] | 6.37 |
| [server/tests/test_browser_keyboard.py::test_arrow_navigation_keeps_fold_animation_running][final-source-2] | 6.31 |
| [static/tests/test_json_collapse.py::test_json_over_text_limit_previews_and_browses\[scalar-8388606\]][final-source-5] | 6.07 |
| [server/tests/test_browser_keyboard.py::test_arrowright_preview_preserves_layout\[click-viewport1\]][final-source-2] | 5.95 |
| [server/tests/test_browser_keyboard.py::test_arrowright_preview_preserves_layout\[click-viewport0\]][final-source-2] | 5.89 |
| [server/tests/test_browser_keyboard.py::test_arrowright_preview_preserves_layout\[click-viewport2\]][final-source-2] | 5.86 |
| [static/tests/test_rich.py::test_rst][final-source-6] | 5.72 |
| [server/tests/test_browser_keyboard.py::test_arrowright_preview_preserves_layout\[keyboard-viewport1\]][final-source-2] | 5.54 |
| [server/tests/test_browser_keyboard.py::test_mobile_landscape_folder_tap_never_folds_touched_column][final-source-2] | 5.43 |
| [server/tests/test_browser_keyboard.py::test_vertical_navigation_keeps_focused_column_whole\[2-1400\]][final-source-2] | 5.35 |
| [server/tests/test_browser_keyboard.py::test_arrowright_preview_preserves_layout\[keyboard-viewport0\]][final-source-2] | 5.29 |

## Delivery commits

The canonical start move is `8b9a0149ba019d03287cbe353fb72adde6b2a454`.
The task delivery history follows, oldest first. Earlier deliveries were
already in the refreshed integration base; the receipt separately records
the latest delivery range. Every check above tests the final merged commit.

- **`01628a5e6469f5165d15286c2e37c7d2ce48a0f8`** — docs(tasks): plan HAI-156 suite qualification
- **`981e4d538115f8b6da7ebcb941036b385ec30ab4`** — fix(tests): qualify bounded root suite shards
- **`f4210f8af08104d9b9c55efbc64161b9b8623936`** — test(ui): wait for pending dial work
- **`c83e31bde2c24033f33b52687f030cc777e1a0c8`** — fix(native): resolve replaced click targets
- **`0a352c1b866d88fb86d7f8937952de1753b9fe17`** — test(ui): drive loading and flings explicitly
- **`a321b63ca21e94af87c706ab938a6086ac511e9c`** — test(server): wait for UI readiness during navigation
- **`a63d83953332099fd9f705836f94000e8c53fe32`** — test(ui): hold stale directory reads until refresh starts
- **`d1a5890da3b740d0659081ff280be53cb188e6e3`** — test(server): use document commit before UI predicates
- **`761fc60ad3cec86e416753d5b532e852a050be2f`** — test(server): isolate deletion refusal routing
- **`6bf6f455d34df17529df7ca5e4410d935e506145`** — test: split served UI evidence into bounded halves
- **`c848215219a36be00b36881f158998944fda98eb`** — docs(test): keep static evidence shards below the target
- **`47cb64dad3d8b506dd1ba7256f217fa93e492e88`** — test(ui): establish a fresh pending rebase before observation
- **`3a76cece1f8dfab684b5f18d64d9ddb9dc3d554a`** — docs(tasks): refresh bounded-suite evidence against current main
- **`aee9c7e22b2db0a4f0e8fbc78b36639c2e328bc2`** — test(ui): finish preview before measuring cached sort reads
- **`f0c0b9eef01596684190538c8331a7bb90b63fe7`** — test(ui): observe focus return after closing copy dialog
- **`14cb7d3b5b77f5955b61750d0f772ed8773fe211`** — test(ui): isolate real layout from controlled clock phases
- **`3f6966a0d8101514c09199f53cc615eeea0a953b`** — test(ui): wait for pending server dial work before input
- **`104a17b82b3cccbc43dc59a984515d1a7d7a8f0c`** — perf(ui): preserve cached column geometry during rendering

<!-- HAI156 final end -->

Steward issue, 2026-10-22 10:45 refill (steward decisions D7 and D95). Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 2.5 h. Unlabelled.

## Why

58 finished filemill items wait in the review queue, the most of any repository. The steward's evidence pass of 2026-10-22 (`<steward-vault>/log/2026-10-22-afternoon-evidence.md`, section "Filemill full suite") could not verify eight of them ([120], [130], [148]–[153]): the documented root command `timeout 1800 uv run pytest` (1,492 tests) was stopped by its bound at 96 %, after one failure marker and with no final summary. The same pass found more red:

- `static/tests/test_ui.py::test_edit_mode` failed in a rerun of the 32 unreported cases (Edit button absent).
- The native UI suite gave 74 passed and five failures: clock and label driver APIs, a native path assertion, render timing, and a delayed-outline selector.
- `server/tests/test_browser_new_ui.py::test_an_offline_copy_of_a_document_is_read_only` is the likely failure marker inside the suite (inferred from collection order) and passed alone.

Older held items fail the same way ("Fix all remaining red tests", [12]). Until one documented command finishes green on this host, no filemill item can be accepted on evidence.

[144] already made the separate static development and bundle suites (185 tests each) pass three times in a row, in 11 to 21 minutes each; read its findings first and don't redo them. This issue is about the root command and the failures above.

## What to do

1. On a clean checkout of `main`, run `timeout 1800 uv run pytest -p no:cacheprovider --junitxml="$TMPDIR/root.xml" --durations=40 -q -rs`. The JUnit file keeps the results if the bound stops the run. Record the wall time, every failure and the 40 slowest tests in this file.
2. Fix each failure at its cause, in the code or the test. Reproduce `test_edit_mode` and the native UI failures. For the offline-copy case, run it after its predecessors in collection order, find the state it inherits, and isolate it.
3. Bring the root run under the bound with margin, aiming at 25 minutes here, by removing waste in the slowest tests: fixed sleeps, repeated browser or server start-ups, duplicated setup. Prefer shared fixtures. If the suite still can't fit, split it in [the test commands] into named shards, each under 25 minutes, whose collected test IDs together equal the root collection exactly (compare `--collect-only -q` output), and say there that evidence runs take them one at a time.
4. Keep the native suite's commands as its guide documents them. Fix its five failures, or state for each, with the failing assertion, why it needs hardware or a display this host lacks.

## Constraints

- Preserve every assertion. Getting to green by skipping, marking xfail, deselecting, retrying or loosening a timeout doesn't count. Leave the 1,800-second bound as it is.
- No new dependency unless it removes more than it adds; say why here.
- Memory: follow your launch prompt's memory rule. Run one heavy command (suite, browser, build) at a time, and no parallel whole-suite run: that is [141], which stopped on swap growth.
- Don't restart the filemill services.
- [141] owns the server keyboard helper's browser lifecycle and the parallel-run qualification. Leave both alone unless a failure here needs the same fix; then say so in both task files.

## Acceptance

- On the merged `main`, the root command (or each documented shard, one at a time) exits 0 with a final pytest summary inside its bound on this host, and `timeout 1800 uv run pytest static/tests --dev` passes too. Wall times before and after are recorded here.
- `test_edit_mode`, the offline-copy case and the five native UI cases pass, or each remaining native case has its stated hardware cause and failing assertion.
- The commits are named here. Handoff: a short outcome; details stay in this file.

Tracker: [filemill's tracker].

## Work history

The implementation plan, clean-main baseline, reproductions and repairs
are in [the work history].

<!-- HAI156 memory start -->
## Memory guard evidence

Readings are MiB. Each command waits at most 600 s for 2,048 MiB;
the fallback requires 1,536 MiB. The guard stops commands and children
below 1,024 MiB or above 512 MiB swap growth. Each test/build command
is bounded by 1,800 s. All heavy commands run sequentially.

The baseline stopped at its runtime bound. All other outcomes below
distinguish a completed command from a passing check. Expected red
probes and actual failed checks retain their nonzero exits.

| Command/run | Outcome | Wait s | Available in/out | Swap start/growth | Peak growth | Elapsed s | Exit |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline-root | stopped while running | 0.0 | 2837/3186 | 2131/+239 | 321 | 1802.3 | 124 |
| browser-red | started at once | 0.0 | 3176/3077 | 2364/+1 | 2 | 22.1 | 0 |
| native-build | started at once | 0.0 | 3027/3079 | 2328/-2 | 4 | 19.1 | 0 |
| native-red | started at once | 0.0 | 3082/2461 | 2322/+15 | 17 | 162.6 | 1 |
| controlled-red | started at once | 0.0 | 2804/2879 | 2222/-1 | 0 | 12.0 | 1 |
| controlled-green | started at once | 0.0 | 2764/2720 | 2230/+0 | 0 | 16.0 | 0 |
| collections | started at once | 0.0 | 2940/2831 | 2229/-2 | 0 | 7.0 | 0 |
| rebuild | started at once | 0.0 | 2906/2869 | 2210/+10 | 10 | 16.0 | 0 |
| native-green | started at once | 0.0 | 2674/2740 | 2206/+33 | 35 | 102.2 | 1 |
| native-label-green | started at once | 0.0 | 2809/2617 | 2190/+5 | 6 | 18.1 | 0 |
| served-ui-order | started at once | 0.0 | 2627/2950 | 2191/+148 | 148 | 751.8 | 0 |
| premerge-gate | started at once | 0.0 | 2971/2951 | 2329/-3 | 0 | 1.0 | 1 |
| premerge-checks | started at once | 0.0 | 2907/2768 | 2318/+20 | 20 | 71.2 | 0 |
| final-keyboard | started at once | 0.0 | 3048/2638 | 2387/-135 | 11 | 417.0 | 0 |
| final-served-ui | started at once | 0.0 | 2837/2991 | 2250/+25 | 215 | 1321.6 | 0 |
| final-server-contracts | started at once | 0.0 | 2998/2916 | 2270/-1 | 0 | 58.1 | 0 |
| final-static-bundle | started at once | 0.0 | 2916/3016 | 2269/+159 | 381 | 1246.0 | 1 |
| rebase-red | started at once | 0.0 | 2703/2566 | 2398/-1 | 1 | 19.2 | 1 |
| rebase-green | started at once | 0.0 | 2702/2788 | 2393/-4 | 0 | 55.3 | 0 |
| rebase-build | started at once | 0.0 | 3103/3087 | 2248/-28 | 0 | 62.2 | 0 |
| rebase-native | started at once | 0.0 | 3022/2848 | 2220/+9 | 9 | 124.5 | 0 |
| rebase-gate | started at once | 0.0 | 3116/3109 | 2225/-2 | 0 | 58.3 | 0 |
| v2-native-build | started at once | 0.0 | 3065/2839 | 2235/+66 | 66 | 59.2 | 0 |
| v2-native-ui | started at once | 0.0 | 2949/3307 | 2301/-56 | 4 | 843.0 | 1 |
| detach-red | started at once | 0.0 | 3166/3272 | 2242/-1 | 0 | 24.1 | 1 |
| detach-green | started at once | 0.0 | 3199/3283 | 2228/-2 | 0 | 36.1 | 0 |
| native-remainder | started at once | 0.0 | 3066/2938 | 2193/-2 | 2 | 197.6 | 0 |
| detach-gate | started at once | 0.0 | 3271/3215 | 2422/-15 | 0 | 9.0 | 1 |
| portable-gate | started at once | 0.0 | 2268/2532 | 2353/-48 | 0 | 92.5 | 0 |
| v3-native-build | started at once | 0.0 | 2873/2710 | 2284/+2 | 5 | 36.0 | 0 |
| v3-native-contracts | started at once | 0.0 | 2733/2873 | 2286/+60 | 60 | 143.7 | 0 |
| v3-native-ui | started at once | 0.0 | 2873/2096 | 2346/-7 | 83 | 517.9 | 1 |
| spinner-red | started at once | 0.0 | 2320/2228 | 2501/+21 | 26 | 16.1 | 1 |
| spinner-green | started at once | 0.0 | 2294/2408 | 2554/+79 | 79 | 35.2 | 0 |
| native-ui-qa | started at once | 0.0 | 2769/2378 | 2431/-232 | 0 | 340.9 | 1 |
| fold-trace | started at once | 0.0 | 2314/2005 | 2181/+8 | 12 | 122.4 | 0 |
| fling-red | started at once | 0.0 | 2742/2598 | 2174/+0 | 0 | 5.0 | 1 |
| fling-green | started at once | 0.0 | 2856/2792 | 2154/-1 | 0 | 36.2 | 0 |
| native-ui-qa2 | started at once | 0.0 | 2786/2731 | 2152/+2 | 15 | 593.4 | 0 |
| fixture-gate | started at once | 0.0 | 2841/2570 | 2151/+1 | 2 | 44.1 | 0 |
| v4-static-bundle | started at once | 0.0 | 3070/2926 | 2181/-37 | 90 | 990.7 | 0 |
| v4-static-dev | started at once | 0.0 | 2937/2815 | 2144/+39 | 198 | 1211.2 | 0 |
| v4-native-build | started at once | 0.0 | 2817/2871 | 2178/-2 | 0 | 42.0 | 0 |
| v4-native-contracts | started at once | 0.0 | 2873/3140 | 2176/+34 | 34 | 78.2 | 0 |
| v4-native-ui | started at once | 0.0 | 3149/3247 | 2210/+136 | 191 | 897.8 | 0 |
| v4-keyboard | started at once | 0.0 | 3248/2849 | 2341/-123 | 0 | 581.1 | 0 |
| v4-served-ui | started at once | 0.0 | 2849/3199 | 2214/+3 | 86 | 1140.7 | 1 |
| navigation-red | started at once | 0.0 | 3174/3181 | 2204/+6 | 6 | 12.0 | 1 |
| navigation-red-controlled | started at once | 0.0 | 3301/3222 | 2209/+0 | 0 | 21.1 | 1 |
| navigation-green | started at once | 0.0 | 3221/3260 | 2209/+7 | 7 | 43.2 | 0 |
| navigation-gate | started at once | 0.0 | 3254/3213 | 2205/+8 | 10 | 15.0 | 0 |
| v5-served-ui | started at once | 0.0 | 3300/3121 | 2210/+72 | 150 | 980.6 | 0 |
| v5-server-contracts | started at once | 0.0 | 3092/3192 | 2276/+0 | 0 | 25.0 | 0 |
| v5-collections | started at once | 0.0 | 3129/3153 | 2275/+0 | 0 | 8.0 | 0 |
| v5-quality | started at once | 0.0 | 2950/3197 | 2273/+0 | 0 | 6.0 | 0 |
| v5-keyboard | started at once | 0.0 | 3193/2494 | 2273/+20 | 24 | 391.2 | 0 |
| v5-static-bundle | started at once | 0.0 | 2717/2838 | 2171/+89 | 234 | 880.5 | 0 |
| v5-static-dev | started at once | 0.0 | 2571/2856 | 2263/-73 | 328 | 1512.9 | 0 |
| v5-native-build | started at once | 0.1 | 2829/2977 | 2124/-8 | 0 | 42.0 | 0 |
| v5-native-contracts | started at once | 0.0 | 3082/3117 | 2116/+1 | 1 | 46.0 | 0 |
| v5-native-ui | started at once | 0.0 | 3163/2503 | 2116/+92 | 173 | 823.3 | 1 |
| refresh-native-green | started at once | 0.0 | 2407/2439 | 2186/-118 | 11 | 131.5 | 1 |
| refresh-diagnostic | started at once | 0.0 | 2200/2370 | 2061/+3 | 3 | 52.3 | 0 |
| refresh-native-diagnostic | started at once | 0.0 | 2223/2508 | 2037/+57 | 62 | 160.8 | 1 |
| refresh-native-gated | started at once | 0.0 | 2574/3161 | 2087/+7 | 136 | 127.6 | 0 |
| refresh-browser-gate | started at once | 0.0 | 2770/3016 | 2064/-14 | 0 | 54.1 | 0 |
| v6-native-build | started at once | 0.0 | 2365/2458 | 2044/+26 | 31 | 68.3 | 0 |
| v6-native-contracts | started at once | 0.0 | 2303/2585 | 2069/+133 | 133 | 181.9 | 0 |
| v6-native-ui | started at once | 0.0 | 2593/2335 | 2199/+124 | 280 | 1040.4 | 0 |
| v6-served-ui | started at once | 0.0 | 2323/2084 | 2309/+104 | 99 | 42.3 | 1 |
| navigation-commit-green | started at once | 0.0 | 2422/2817 | 2584/-229 | 37 | 130.4 | 0 |
| navigation-commit-gate | started at once | 0.0 | 2817/2770 | 2355/-11 | 0 | 9.8 | 0 |
| v7-served-ui | started at once | 0.0 | 2780/2108 | 2336/+74 | 209 | 783.0 | 1 |
| delete-routed-green | started at once | 0.0 | 2067/2100 | 2372/+37 | 40 | 43.4 | 0 |
| delete-response-green | started at once | 0.0 | 2267/2089 | 2406/+0 | 0 | 18.1 | 0 |
| delete-route-gate | started at once | 0.0 | 2228/2150 | 2404/-3 | 0 | 21.1 | 0 |
| v8-served-ui | stopped while running | 22.0 | 2155/2349 | 2507/+56 | 430 | 1800.5 | 124 |
| partition-red | started at once | 0.0 | 2716/2724 | 2458/+0 | 0 | 4.0 | 1 |
| partition-green | started at once | 0.0 | 2765/2752 | 2454/-1 | 0 | 2.0 | 0 |
| partition-collections | started at once | 0.0 | 2777/2598 | 2451/+0 | 0 | 15.1 | 0 |
| partition-gate | started at once | 0.0 | 2668/2618 | 2439/-3 | 0 | 13.1 | 1 |
| partition-gate-green | started at once | 0.0 | 2517/2528 | 2455/+5 | 5 | 18.1 | 0 |
| v9-served-ui-early | started at once | 0.0 | 2693/2303 | 2494/+136 | 313 | 562.9 | 0 |
| v9-served-ui-late | started at once | 0.0 | 2307/2822 | 2628/+104 | 412 | 1011.2 | 0 |
| v9-server-contracts | started at once | 0.0 | 2808/2773 | 2720/-18 | 0 | 73.3 | 0 |
| v9-collections | started at once | 0.0 | 2795/2777 | 2699/-97 | 0 | 26.1 | 0 |
| v9-quality | started at once | 0.0 | 2867/2952 | 2585/+13 | 14 | 17.1 | 0 |
| v9-keyboard | started at once | 0.0 | 2929/2075 | 2629/+183 | 251 | 953.1 | 0 |
| v9-static-bundle | started at once | 0.0 | 2086/2645 | 2806/-482 | 318 | 1772.2 | 0 |
| v9-static-dev | started at once | 0.0 | 2640/2677 | 2317/+20 | 73 | 1246.4 | 0 |
| static-partition-gate | started at once | 0.0 | 2093/2173 | 2376/+19 | 22 | 91.5 | 0 |
| v10-static-adapters | started at once | 0.0 | 2075/2970 | 2390/-73 | 509 | 607.6 | 0 |
| v10-static-ui | started at once | 0.0 | 2994/2936 | 2312/-10 | 0 | 45.1 | 1 |
| rebase-probe-green | started at once | 0.0 | 3082/3077 | 2297/+0 | 3 | 39.0 | 0 |
| rebase-probe-gate | started at once | 0.0 | 2854/2611 | 2249/-2 | 6 | 87.4 | 0 |
| static-ui-probe-qa | started at once | 0.0 | 2589/2825 | 2247/+166 | 213 | 698.3 | 0 |
| rebase-probe-docs | started at once | 0.0 | 2722/2690 | 2339/-8 | 0 | 12.0 | 0 |
| v11-static-ui | started at once | 0.0 | 2787/2576 | 2279/-12 | 0 | 509.5 | 0 |
| v11-native-build | started at once | 0.0 | 2571/2487 | 2267/+35 | 36 | 35.1 | 0 |
| v11-native-contracts | started at once | 0.0 | 2467/2636 | 2301/+72 | 72 | 81.2 | 0 |
| v11-native-ui | started at once | 0.0 | 2713/2707 | 2361/+108 | 176 | 667.8 | 0 |
| v11-static-dev | started at once | 0.0 | 2749/2673 | 2457/-25 | 228 | 1614.6 | 0 |
| v11-static-adapters | started at once | 0.0 | 2596/2245 | 2416/+329 | 405 | 932.8 | 0 |
| v11-keyboard | started at once | 0.0 | 2224/2493 | 2751/-263 | 182 | 671.9 | 0 |
| v11-served-ui-early | started at once | 0.0 | 2566/2649 | 2486/+29 | 32 | 338.8 | 0 |
| v11-served-ui-late | started at once | 0.0 | 2737/2853 | 2514/+190 | 347 | 650.2 | 0 |
| v11-server-contracts | started at once | 0.0 | 2861/2764 | 2697/-25 | 0 | 46.2 | 0 |
| v11-collections | started at once | 0.0 | 2946/2804 | 2668/-2 | 0 | 16.0 | 0 |
| v11-quality | started at once | 0.0 | 2810/2770 | 2661/+0 | 0 | 9.0 | 0 |
| main-docs-integration-gate | started at once | 0.0 | 2933/2716 | 2539/-1 | 0 | 22.0 | 0 |
| v12-server-contracts | started at once | 0.0 | 2725/2764 | 2514/-8 | 0 | 51.1 | 0 |
| v12-collections | started at once | 0.0 | 2773/2685 | 2506/+0 | 0 | 13.0 | 0 |
| v12-quality | started at once | 0.0 | 2773/2732 | 2506/+0 | 0 | 9.0 | 0 |
| v12-static-dev | started at once | 0.0 | 2941/2922 | 2505/-13 | 3 | 562.9 | 0 |
| v12-static-ui | started at once | 0.0 | 3043/3040 | 2491/+104 | 106 | 309.2 | 0 |
| v12-static-adapters | started at once | 0.0 | 3023/3001 | 2591/+80 | 97 | 267.4 | 0 |
| v12-native-build | started at once | 0.0 | 3073/3063 | 2660/+1 | 3 | 15.0 | 0 |
| v12-native-contracts | started at once | 0.0 | 3100/3201 | 2659/+32 | 32 | 43.1 | 0 |
| v12-native-ui | started at once | 0.0 | 3333/2855 | 2691/+17 | 22 | 421.8 | 1 |
| cached-sort-native-green | started at once | 0.0 | 3275/3360 | 2598/+53 | 53 | 49.1 | 0 |
| cached-sort-qualification | started at once | 0.0 | 3455/3422 | 2658/-14 | 0 | 195.4 | 1 |
| cached-sort-commit-gate | started at once | 0.0 | 3421/3422 | 2603/+0 | 0 | 10.1 | 0 |
| copy-focus-green | started at once | 0.0 | 3408/3308 | 2602/-1 | 0 | 38.1 | 0 |
| native-readiness-qa | started at once | 0.0 | 3406/3024 | 2598/+5 | 15 | 600.2 | 0 |
| v13-native-build | started at once | 0.0 | 3249/3132 | 2596/-6 | 0 | 14.0 | 0 |
| v13-native-contracts | started at once | 0.0 | 3248/3058 | 2590/-8 | 0 | 52.2 | 0 |
| v13-native-ui | started at once | 0.0 | 3046/3100 | 2582/-14 | 0 | 37.0 | 1 |
| clock-boundary-green | started at once | 0.0 | 3112/3077 | 2563/+9 | 9 | 79.1 | 0 |
| clock-fixture-native-qa | started at once | 0.0 | 3124/3187 | 2568/+56 | 85 | 642.5 | 0 |
| v14-native-build | started at once | 0.0 | 2870/2819 | 2596/-165 | 6 | 20.0 | 0 |
| v14-native-contracts | started at once | 0.0 | 2896/2708 | 2430/+28 | 33 | 80.3 | 0 |
| v14-native-ui | started at once | 0.0 | 2969/3037 | 2471/+9 | 71 | 745.1 | 0 |
| v14-static-ui | started at once | 0.0 | 3092/2490 | 2476/-62 | 0 | 429.0 | 0 |
| v14-static-dev | started at once | 0.0 | 2738/2727 | 2414/-5 | 1 | 682.5 | 0 |
| v14-static-adapters | started at once | 0.0 | 2732/2748 | 2409/+11 | 13 | 245.4 | 0 |
| v14-keyboard | started at once | 0.0 | 2906/2513 | 2420/-13 | 0 | 346.6 | 1 |
| keyboard-tap-green | started at once | 0.0 | 2495/2578 | 2404/+0 | 1 | 53.1 | 0 |
| server-input-qa | started at once | 0.0 | 3151/3089 | 2358/+5 | 29 | 388.7 | 0 |
| v15-keyboard | started at once | 0.0 | 3306/3384 | 2373/+25 | 32 | 331.6 | 0 |
| v15-served-ui-early | started at once | 0.0 | 3404/3062 | 2397/-11 | 0 | 310.6 | 0 |
| v15-served-ui-late | started at once | 0.0 | 3127/3062 | 2385/+21 | 21 | 389.8 | 0 |
| v15-native-build | started at once | 0.0 | 3409/3296 | 2405/+14 | 14 | 14.0 | 0 |
| v15-native-contracts | started at once | 0.0 | 3263/3486 | 2417/+19 | 20 | 41.1 | 0 |
| v15-native-ui | started at once | 0.0 | 3486/2801 | 2435/+138 | 200 | 593.5 | 1 |
| v15-static-ui | started at once | 0.0 | 2826/2760 | 2564/-81 | 74 | 432.0 | 0 |
| v15-static-dev | started at once | 0.0 | 2877/3009 | 2482/-20 | 0 | 581.2 | 0 |
| v15-static-adapters | started at once | 0.0 | 3100/2973 | 2462/-16 | 1 | 245.4 | 0 |
| v15-server-contracts | started at once | 0.0 | 3113/3064 | 2446/-2 | 0 | 17.0 | 0 |
| v15-collections | started at once | 0.0 | 3175/3110 | 2444/+0 | 0 | 8.0 | 0 |
| v15-quality | started at once | 0.0 | 3097/3008 | 2443/+0 | 0 | 4.0 | 0 |
| cached-classes-red | started at once | 0.0 | 3055/2896 | 2441/-1 | 0 | 5.0 | 1 |
| cached-classes-green | started at once | 0.0 | 3001/2875 | 2440/+0 | 0 | 11.0 | 0 |
| cached-classes-native-green | started at once | 0.0 | 3016/3155 | 2440/+2 | 2 | 46.1 | 1 |
| cached-classes-native-built | started at once | 0.0 | 3153/3169 | 2442/+14 | 14 | 47.0 | 0 |
| cached-classes-quality | started at once | 0.0 | 3183/3142 | 2455/+0 | 0 | 3.0 | 1 |
| cached-classes-bundle-quality | started at once | 0.0 | 3171/3174 | 2455/+0 | 0 | 1.0 | 2 |
| cached-classes-final-quality | started at once | 0.0 | 3165/3127 | 2455/+0 | 0 | 5.0 | 0 |
| v16-native-build | started at once | 0.0 | 3147/3028 | 2447/+1 | 1 | 9.0 | 0 |
| v16-native-contracts | started at once | 0.0 | 3162/3064 | 2447/+1 | 1 | 40.0 | 0 |
| v16-native-ui | started at once | 0.0 | 3086/3438 | 2447/+63 | 132 | 487.9 | 0 |
| v16-keyboard | started at once | 0.0 | 3439/3356 | 2508/-24 | 0 | 326.7 | 0 |
| v16-served-ui-early | started at once | 0.0 | 3408/3151 | 2484/-3 | 10 | 313.7 | 0 |
| v16-served-ui-late | started at once | 0.0 | 3353/3222 | 2479/-14 | 0 | 377.7 | 0 |
| v16-static-ui | started at once | 0.0 | 3327/3204 | 2465/-10 | 0 | 297.5 | 0 |
| v16-static-dev | started at once | 0.0 | 3208/3465 | 2455/-41 | 0 | 577.0 | 0 |
| v16-static-adapters | started at once | 0.0 | 3102/3193 | 2417/+41 | 51 | 245.3 | 0 |
| v16-server-contracts | started at once | 0.0 | 3238/3245 | 2458/+0 | 0 | 24.0 | 0 |
| v16-collections | started at once | 0.0 | 3313/3243 | 2457/+0 | 0 | 8.0 | 0 |
| v16-quality | started at once | 0.0 | 3314/3242 | 2457/+0 | 0 | 4.0 | 0 |
| final-docs | started at once | 0.0 | 3285/3219 | 2446/+0 | 0 | 3.0 | 0 |

Exact argument vectors are in [the guarded command arguments].
Run names match that artifact and [the memory log].
<!-- HAI156 memory end -->


[12]: 12-test-ui-runs-to-end.md
[144]: 144-make-the-full-static-suites-pass-reliably-the-wide-folder-wait-and-tes.md
[120]: 120-disable-server-search-in-local-folders-from-docs-question-5.md
[130]: 130-give-served-and-browser-owned-folders-the-same-content-search.md
[141]: 141-finish-browser-fixture-isolation-and-qualify-independent-test-roots.md
[the memory log]: http://hopeli/tmp/filemill-hai156/memory.jsonl?f
[the run directory]: http://hopeli/tmp/filemill-hai156/?f
[the test commands]: ../../CONTRIBUTING.md#tests
[filemill's tracker]: ../../TASKS.md
[the guarded command arguments]: http://hopeli/tmp/filemill-hai156/commands.json?f
[final-test-commands]: ../../CONTRIBUTING.md#tests
[final-receipt]: 156-make-filemill-s-root-suite-finish-green-within-its-30-minute-bound-on-.evidence.json
[final-source-1]: ../../static/tests/test_ui.py
[final-source-2]: ../../server/tests/test_browser_keyboard.py
[final-source-3]: ../../server/tests/test_browser_new_ui.py
[final-source-4]: ../../static/tests/test_url.py
[final-source-5]: ../../static/tests/test_json_collapse.py
[final-source-6]: ../../static/tests/test_rich.py
[the work history]: 156-root-suite-work-history.md
