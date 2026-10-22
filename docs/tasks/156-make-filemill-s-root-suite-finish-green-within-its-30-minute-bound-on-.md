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

## Served navigation readiness

The fourth merged recording passed static bundle (193), static development
(193), native contracts (20), native UI (83), and keyboard (67). The served
UI shard then stopped with 288 passed and one failure in
`test_json_column_refresh_current_source[invalid-False-True]`: `Page.goto:
Timeout 3000ms exceeded`, while waiting for the full `load` event. Guard
wall time was 1,140.7 s. The remaining 23 served cases and later queued
checks were not run. The fourth failed receipt retains these results.

The short test timeout also applied to navigation. A controlled regression
holds an unrelated image request while the UI is already ready. With service
workers blocked so routing takes effect, the original harness reproduced the
same 3,000 ms navigation failure (7.24 s pytest time). The initial probe did
not block service workers and failed its route-observation assertion instead;
that setup error is retained in the logs.

The harness now waits for `DOMContentLoaded`, followed by the same path,
selection, cached-column, spinner, row and loaded-font predicates. No assertion
or timeout is relaxed. The held image remains pending when the UI assertions
succeed. This proves excess load-event coupling; the failed full run did not
identify which resource or scheduling delay held its load event.
The controlled case and all 12 JSON-refresh variants then passed together:
13 passed in 41.20 s (guard wall 43.2 s).

## Refresh race observation

At `a321b63c`, all four root shards passed: 67 keyboard, 313 served UI,
924 server contracts and 193 static bundle cases. Their 1,497 collected IDs
matched root pytest exactly, with multiplicity. The longest root shard took
980.6 s including recording overhead. Static development also passed all
193 cases in a 1,512.9 s guarded command. Native build, 20 native contracts,
collection comparison and the complete quality gate passed.

The final native UI command stopped with 69 passed and one failure in
`test_refresh`: `TimeoutError: path[1]?.loading`. Thirteen later cases were
unreported. Pytest elapsed time was 811.53 s; guarded wall time was 823.3 s.
The racing-directory fixture exposed its in-flight read for only 400 ms,
which native click/observation round trips can miss. This is a test-input
lifetime failure, not a missing display or hardware capability.

The racing read now snapshots entries and waits on a test-owned release
promise in both fake and native adapters. The test observes loading, adds
the third file, starts refresh without awaiting its intentionally blocked
promise, and releases the old read in `finally`. It then awaits refresh
and retains the exact three-file order, count and cleared-loading assertions.
The second read is not artificially delayed. No production port, assertion
or timing bound changes. The fifth failed receipt preserves the full result.

The first gate implementation also failed: its readiness expression returned
the release function, which the wait helper invoked as a predicate, releasing
the read. A direct native probe showed the gate installed with loading true;
the full diagnostic confirmed the same state before that wait. The predicate
now returns a boolean type check instead. Both unsuccessful probes remain
in the memory log; their passes are not claimed.

The complete focused refresh scenario passed in native (85.90 s), development
(17.28 s) and bundle (16.81 s) modes. All seven quality hooks, explicit Python
lint/format checks and 28 documentation/readiness checks also passed. The
next clean merged recording starts with the full native UI command.

## Navigation commit boundary

At `a63d8395`, native build, all 20 contracts and all 83 native UI cases
passed. Native UI guarded wall time was 1,040.4 s. The served UI run then
failed its first controlled navigation case: `Page.goto: Timeout 3000ms
exceeded`, waiting for `domcontentloaded`. The seventeen-minute native pass
is preserved in the sixth failed recording; later queued checks did not run.

Waiting for that browser lifecycle event still couples initial navigation
to parsing/executing the complete deferred resource graph. The harness now
returns from navigation at document commit and uses its existing UI readiness
predicates. Every configured timeout remains unchanged, including 3,000 ms
in the controlled regression and JSON-refresh cases. The controlled case
and all 12 JSON-refresh variants passed together in 94.46 s on this host.
The held-image assertion and all application readiness predicates remain.

## Routed deletion failure input

At `d1a5890d`, the served UI shard stopped with 214 passed and one failure
in `test_context_menu_delete_failure_and_virtual_entry`: its 30,000 ms wait
for `Delete failed: test denied` expired. Guarded wall time was 783.0 s;
pytest elapsed time was 777.84 s. The remaining 98 cases and later queued
checks did not run. The seventh failed receipt preserves this result.

The failure-injection case used the normal service-worker-enabled page,
unlike the module's other request-routing tests. It now uses the existing
routed-page fixture and verifies the exact injected HTTP 403 JSON response
before checking the message. All original row, file and virtual-entry
assertions remain. The failed run did not capture the response or final
status text, so worker interference is an isolation concern, not a proven
reconstruction of that run. The worker excludes non-GET requests itself;
no production worker behavior is changed. Dedicated worker tests still run.

The case and four related deletion cases passed together (5 in 38.62 s).
After adding the explicit response assertions, the focused case passed in
14.41 s. This response check makes a failed injection observable directly.

## Split the oversized served UI shard

At `761fc60a`, the refusal case and injected-response assertions passed in
collection order. The served UI command then reached its unchanged 1,800 s
bound with no failure marker, at approximately 82% progress. Exit was 124;
guarded wall time was 1,800.5 s after a 22.0 s admission wait. It did not
produce a final pytest summary or JUnit report. This is an incomplete stopped
check, not a pass or unavailable recording. Later queued checks did not run.

Earlier complete served runs took 980.6–1,321.6 s including recording. That
margin did not hold under this host load. The documented command set now
has five root shards: keyboard, served UI early, served UI late, server
contracts and static bundle. The served module is split into ordered halves
by its collected item count. The option refuses other modules. Both halves
must run; the other half is reported as deselected by each command, and no
case is omitted from the combined evidence. Default root collection is
unchanged. No retry, skip, xfail or timeout increase is introduced.

Three partition contracts failed before the hook existed (0.39 s), then all
passed (0.08 s). They check odd-sized coverage, order, duplicate-free object
membership, and rejection of mixed-module collections. The real collection
comparison passed: 1,500 root IDs equal 67 keyboard + 157 served early +
156 served late + 927 contracts + 193 static bundle IDs, with multiplicity.
The three new partition contracts account for the latest count increase.
No dependency is added. Existing browser/server fixtures remain shared
within each command. The offline-copy predecessor diagnostic remains in
the earlier full-module run; no leaked state was found there.

## Static evidence margin

At `6bf6f455`, both served halves, keyboard, all 927 server contracts,
collection comparison and the quality gate passed. Static bundle passed
all 193 cases in 1,736.28 s pytest time (1,772.2 s guarded wall time).
It fit the 1,800 s bound but missed the 25-minute shard target. Development
passed all 193 cases in 1,207.10 s (1,246.4 s guarded wall time).

The final root command set therefore has six shards. Static UI runs its
83 cases separately from the remaining 110 static adapter/model cases.
The full development command remains unchanged. This keeps the existing
fresh-browser and fresh-context isolation from [static reliability] and
makes no fixture lifecycle change. The final collection comparison must
still prove coverage of all 1,500 root IDs, including duplicates.

The queued native build and later native checks were deliberately not
started in this recording round, so the final documented partition can be
merged before further recording. They are deferred, not failed native
checks. Earlier complete native qualifications remain historical evidence;
complete final recording is still required. The partial green receipt and
all duration logs are retained in the run directory. No dependency, skip,
xfail, application assertion or timeout changes accompany this split.

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
[static reliability]: 144-make-the-full-static-suites-pass-reliably-the-wide-folder-wait-and-tes.md
