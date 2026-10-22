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

## Implementation plan, 2026-10-22

1. Measure a clean-main root run with the requested flags and a memory guard.
   Keep this baseline unchanged until it exits or reaches its bound.
2. Reproduce Edit readiness and the five native failures. Use controlled
   asynchronous work for regressions. Preserve assertions and timing bounds.
3. Run the offline-copy test after its collection predecessors. Investigate
   inherited state separately from within-test asynchronous work.
4. Use measured durations to remove waste or document exhaustive sequential
   shards. Compare collected IDs, including multiplicity, against root pytest.
5. Run the quality gate, merge, and record checks from a clean merged checkout.
   Complete the tracker only after acceptance checks pass.

The start move is commit `8b9a0149`. The baseline starts at that clean main
commit. No dependency or service change is planned. The keyboard fixture
lifecycle and parallel qualification remain owned by [fixture isolation].

## Clean-main baseline

The requested root command at `8b9a0149` reached its unchanged 1,800-second
bound and exited 124. The guard finished cleanup after 1,802.3 seconds. The
last progress label was 91%; 1,391 result markers were emitted, with one
failure at ordinal 399. This is an incomplete failed run, not a pass.

Pytest did not write the requested JUnit file before termination: its plugin
writes during session teardown. No final traceback, summary or 40-slowest
report exists for this baseline. A failure name inferred from collection
order is not a recovered traceback. Completed diagnostic and shard runs
will supply the missing failure and timing detail separately.

The historical steward root run reached 96% within the same bound. Current
server tests alone consumed about 26 minutes before static tests began.
Use separate keyboard, shared-UI, server-contract and static shards, each
with the original bound. Validate their collected IDs against root pytest,
including duplicate counts. Run all shards sequentially for evidence.

The baseline memory outcome was **stopped while running** (runtime bound,
not memory pressure): admission wait 0.0 s; available 2,837 / 3,186 MiB;
starting swap 2,131 MiB; final growth +239 MiB (peak +321 MiB); exit 124.
The raw command output is in [the baseline log]; measurements are in
[the memory log]. Neither log is a successful acceptance receipt.

## Reproductions and repairs

All five native failures reproduced in one focused run: 5 failed in 154.12 s.
No hardware or display gap explains them. The documented native shell builds
and Xvfb work here.

- **Wheel axis:** `NativePage.clock` was absent. The shared check now waits for
  observable scroll settlement rather than requiring an engine-specific clock.
  Its directional-movement assertion is unchanged.
- **Remount route:** `assert "p=deep" in location.hash` failed because native
  routing lives in the router port, not the browser hash. Native checks now
  assert the same old and new paths through that port. Browser hash assertions
  remain, and the snapshot compares both the URL and router state.
- **Copy label:** `NativePage.get_by_label` was absent. The driver now resolves
  the HTML label's associated control, with an ARIA-label fallback. An initial
  ARIA-only attempt failed because this dialog uses `label[for]`; the corrected
  focused Copy check is required before qualification.
- **Render cost:** `134.4 < (31.8 + 100)` failed after the 3,000-file sweep,
  while the exact column-identity and read-count checks succeeded. Render was
  sorting the children again through `rowIndex`, after obtaining a cached
  ordered column. It now finds the selection in that column's children.
  No budget or timing assertion changed.
- **Delayed outline:** `.row[title="plain.md"]` timed out. The test mounted an
  in-memory FSA handle directly, which the native port cannot read. The fixture
  now materializes its file through the shared mounting helper, then delays the
  first Blob text read. All preview-count, pane-identity and Edit assertions
  remain. The driver permits fixture trees without a `locked` directory.

A controlled Edit probe holds the eligibility read after preview text appears.
The original immediate visibility assertion failed. After releasing that read,
the test now waits for Edit readiness before making the same assertion. This
establishes a readiness race; the uninstrumented case passed in isolation.
The regression also asserts Edit stays hidden while eligibility is pending.

A new cached-render regression counts 1,000-child array sorts during render.
It failed with one redundant sort, then passed with zero after the repair.
Both controlled regressions passed together in development mode (14.34 s).
No port or observable application policy changes, so no new ADR is required.
No dependency was added. Keyboard browser lifetime and parallel qualification
remain untouched.

## Collection partition

The first repaired root collection had 1,493 tests, including the new cached-render regression.
The four shards collect 67 keyboard, 312 served UI, 924 server contracts and
190 static bundle tests. Comparing Counters of the complete node IDs gives an
exact multiset match, so no ID is omitted or repeated between shards.
The current collection maps baseline ordinal 399 to
`test_mobile_fullscreen_history_after_preview_change[view]`. That is still an
inference until a traceback reproduces it. All three variants passed alone.

Collection logs and all focused outputs remain in [the run directory].

## Ordered served-UI qualification

The complete served-UI shard passed all 312 tests in 750.77 s (guard wall
751.8 s). This includes the history case at ordinal 225 and the offline-copy
case at ordinal 278 after all their module predecessors. The offline test
creates its own context and writable tree, and starts its own server. No
inherited browser storage or shared-tree mutation was found in this run.

The baseline's inferred history failure did not reproduce in isolation or
module order. Its original traceback was lost at the timeout, so its specific
cause remains unestablished. Shards isolate the roots and allow every test to
finish and report. This is not evidence that the old marker was the offline
case, nor a claim that an unidentified history defect was repaired.

The first focused native correction run passed six of seven checks, including
the unchanged render timing check (36.49 s for that case). Copy then passed
with proper HTML-label resolution (8.25 s). The full native suite remains a
required merged-main check; focused passes do not replace it.

Final acceptance runs use the four documented shards sequentially, plus the
complete static development suite and the documented native commands.
[The evidence receipt] will record the tested merged commit, exact commands,
dependency fingerprints and results. Logs stay outside the clean checkout.

## First merged-main recording failure

At `981e4d53`, keyboard (67 tests), served UI (312) and server contracts
(924) passed. The full static bundle shard finished in 1,226.89 s with
189 passed and one failure: `test_folding_dial` timed out waiting for
`document.querySelectorAll('.col.spine').length === path.length` after the
second fling. Recording stopped there; development, native and remaining
checks were not run in that recording sequence. The failed receipt and JUnit
files are preserved in [the run directory], including
[the first failed receipt]. This failed check is not unavailable evidence.

This is the second-fling wait, distinct from [144]'s historical nested
wide-folder selection wait. The scroll helper considered 300 ms of unchanged
geometry settled, without observing a pending glide or range-rebase callback.
A controlled regression holds the 180 ms rebase callback while advancing a
browser clock through 400 ms of quiet geometry. The old predicate returned
true and failed the new negative assertion. This proves a false-readiness
mechanism; it does not recover the lost state of every historical fold failure.

The shared debug surface now reports whether the dial has pending timers,
glides, scroll writes or held pointer input. The existing helper requires that
state to be idle as well as the original quiet-geometry condition. Its
6,000 ms bound and every folding/clipping assertion remain unchanged. No
application fold policy, port or dependency changes. No new ADR is needed
for this read-only test instrumentation.

The held-rebase probe failed in 13.80 s with the old helper. The corrected
probe and the complete folding-dial test passed together in development mode
(2 passed, 51.70 s). The new regression uses the existing Chromium clock
fixture, including when the native command is used; it does not add a clock
API to the native driver.

Hook installation was refused because `core.hooksPath` is configured. That
setting was preserved. The complete pre-commit gate was run directly and all
seven checks passed before the first merge, along with model checks, explicit
static/native Python lint and formatting, 28 documentation/readiness checks
and seven focused bundle cases. Final merged-main checks remain required.

## Native row replacement during sorting

At `f4210f8a`, the native UI command stopped with 70 passed and one failure
in `test_sort_options`; ten cases were unreported. WebDriver returned
`stale element reference` while clicking the `mixed` row after metadata
completion rebuilt its column. This is a locator-resolution failure, not a
hardware or display limitation. The [second failed receipt] is retained in [the run directory].

A new native contract replaces the resolved row immediately before WebDriver
clicks it. It failed with the same stale-element error (3.78 s). The driver
now releases its old hit interceptor and resolves the locator again inside
the original click deadline. Each visibility wait receives the remaining
action time. No assertion or timeout is relaxed, and no pytest case is
retried by the driver.

The controlled contract and original sorting case then passed together
(2 passed, 28.01 s). The contract also asserts exactly one received click and
the expected navigation. The [native guide] now lists 20 contracts. The ten
unreported UI cases and all contracts are checked before the next merge;
the final recording must still run the complete native UI command.

The ten unreported UI cases and all 20 contracts passed together: 30 passed
in 185.58 s. This includes the original rendering and delayed-outline cases.
The complete native UI command is still required on the next merged commit.

An intermediate memory appendix placed machine-specific argument paths in
Markdown. The portability documentation check rejected it. Exact arguments
now live in a linked JSON artifact; measurements and run names remain here.
The unmodified documentation check then passed, along with every quality
hook, all three changed Python files' lint/format checks and model checks.
Deno is the documented 2.6.8 release.

At that qualification the collection was 1,494: 67 keyboard, 312 served UI, 924 server
contracts and 191 static bundle cases. The streamed Counter comparison
retains duplicate counts and matches root collection exactly.

## Slow-folder indicator observation

At `c83e31bd`, native build and all 20 contracts passed. The native UI command
stopped with 46 passed and one failure in `test_directory_states`: the
`.col[data-i="1"] .spinner` selector was absent at its unchanged 2,000 ms
wait. The fixture completed its slow read after 500 ms, before the native
click/observation round trips finished. The [third failed receipt] is retained;
34 UI cases were unreported in that stopped run.

A controlled browser-clock regression advances past that 500 ms window before
observing the indicator. It failed with the old fixture (9.30 s). The test
input now holds the port read on a promise until the spinner assertion releases
it in `finally`. The original visibility wait and exact two-entry assertion
remain. The clock regression and directory-state case passed together in
development mode (2 passed, 20.10 s). The complete native UI command is now
being qualified before the next merge. This change affects test input only.

## Fling input matches the wheel handler

The first complete native qualification with the spinner gate still failed
the second-fling assertion: 57 passed, one failed, in 329.30 s. The readiness
probe is useful but did not fully explain that failure. A focused geometry
trace passed with dial positions 495, 990 and 1,238 (unit 247.5, range 1,250);
it did not capture the failed ending state.

The old fling input assigned `scrollLeft`, which starts a CSS smooth scroll.
The range-rebase timer can run before that animation reaches its endpoint.
Actual preview wheel input uses the wheel handler's instant scroll instead.
A controlled clock probe advanced the settlement timer before the old CSS
movement arrived and failed with two spines instead of four (3.77 s).

The fling input now dispatches the preview wheel event. The clock probe and
complete folding-dial case passed together in development mode (2 passed,
34.23 s). Every spine-count, unfold and clipping assertion is retained.
Keyboard and spine-unfold moves still exercise their smooth glides. No
application folding arithmetic or timing budget changes.

The complete native UI qualification then passed all 83 cases in 582.18 s
(guard wall 593.4 s), including every originally reported native failure and
the additional cases found here. All quality hooks, explicit Python checks,
model checks and 28 documentation/readiness checks passed afterward.
The streamed collection comparison now matches all 1,496 root IDs: 67
keyboard, 312 served UI, 924 server contracts and 193 static bundle cases.
No assertion, 1,800-second bound or dependency was removed or relaxed.

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

Exact argument vectors are in [the guarded command arguments].
Run names match that artifact and [the memory log].
<!-- HAI156 memory end -->

[12]: 12-test-ui-runs-to-end.md
[144]: 144-make-the-full-static-suites-pass-reliably-the-wide-folder-wait-and-tes.md
[120]: 120-disable-server-search-in-local-folders-from-docs-question-5.md
[130]: 130-give-served-and-browser-owned-folders-the-same-content-search.md
[141]: 141-finish-browser-fixture-isolation-and-qualify-independent-test-roots.md
[fixture isolation]: 141-finish-browser-fixture-isolation-and-qualify-independent-test-roots.md
[the baseline log]: http://hopeli/tmp/filemill-hai156/baseline-root.log?f
[the memory log]: http://hopeli/tmp/filemill-hai156/memory.jsonl?f
[the run directory]: http://hopeli/tmp/filemill-hai156/?f
[The evidence receipt]: 156-make-filemill-s-root-suite-finish-green-within-its-30-minute-bound-on-.evidence.json
[the test commands]: ../../CONTRIBUTING.md#tests
[filemill's tracker]: ../../TASKS.md
[the first failed receipt]: http://hopeli/tmp/filemill-hai156/receipt-981e4d53-failed.json?f
[second failed receipt]: http://hopeli/tmp/filemill-hai156/receipt-f4210f8a-failed.json?f
[native guide]: ../../native/README.md#checks
[the guarded command arguments]: http://hopeli/tmp/filemill-hai156/commands.json?f
[third failed receipt]: http://hopeli/tmp/filemill-hai156/receipt-c83e31bd-failed.json?f
