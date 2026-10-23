# Filemill [156] work history

The implementation history of [the issue description], moved there
unchanged on 2026-10-23 so that the description stays below Hai's
50,000-character limit.

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

## Pending-rebase probe setup

At `c8482152`, the 110-case static adapter shard passed in 607.6 s guarded
wall time. The static UI shard then stopped with eight passed and one
failure in `test_scroll_settlement_waits_for_pending_rebase`: the negative
quiet-geometry assertion observed `True`. Pytest elapsed time was 41.90 s;
guarded wall time was 45.1 s. Seventy-four UI cases and later queued checks
were unreported in this round. The tenth recording retains that failure.

The controlled probe dispatched a synthetic scroll without cancelling any
earlier CSS glide or checking its pending-work precondition. Its held callback
could therefore be stale by the negative assertion; the full failed callback
ordering was not captured. The probe now makes an instant dial move to its
current position, cancelling the earlier glide and scheduling a fresh rebase.
It asserts that the release callback exists and the dial is pending before
advancing the quiet-geometry clock. The original negative and final positive
settlement assertions remain. No production code or timeout changes.

The corrected probe and full folding-dial case passed together in bundle
mode (2 in 36.06 s). The probe also passed in development (16.00 s) and through
the native command's existing Chromium clock fixture (5.02 s). All seven
quality hooks, explicit Python checks and 31 documentation/readiness/partition
checks passed. Complete static UI qualification then passed all 83 cases in 692.66 s
(698.3 s guarded wall time), before the next merge.

## Main documentation integration

All 12 acceptance recordings passed at `47cb64da`, including all 1,500 root
cases, 193 development cases, 20 native contracts and 83 native UI cases.
The longest guarded root shard took 932.8 s; the full development command
took 1,614.6 s. The complete green receipt and JUnit files are retained.

Main advanced during that long recording with [the architecture-summary task].
Its documentation contract adds one root case. The feature branch has now
incorporated that main update. Final recording will include the new contract:
1,501 root cases and 928 server-contract cases, with the other shard counts
unchanged. This integration records task evidence; the other task's files
are retained as delivered. The final receipt uses the refreshed pre-merge
base and preserves the earlier delivery history separately.

## Cached-sort read-count window

At `3a76cece`, updated server contracts (928), collection equality (1,501),
quality, static development (193), static UI (83), static adapters (110),
native build and native contracts (20) passed. Native UI then stopped with
72 passed and one failure in `test_sort_options`: the cached-return assertion
observed `1 further getFile() calls` where `again == 0` was required. Pytest
time was 413.45 s; guarded wall time was 421.8 s. Ten native cases and the
three later browser shards were unreported in this round.

The read-count baseline waited for metadata and selected-path coherence,
while the preceding README preview could still perform its eligibility
snapshot read. Native instrumentation counts that read separately. The
existing preview lifecycle paints text before completing eligibility, as
already reproduced by the Edit regression. The test now waits for the Edit
control to become visible before taking its cached-sort I/O baseline. The
exact row order, five initial reads and zero subsequent reads remain; no
operation is excluded from the counter and no timeout changes.

The complete focused native sorting case passed with that readiness boundary
(26.58 s). Browser sorting checks also passed in development (15.15 s)
and bundle (10.93 s) modes. The full native qualification stopped earlier,
with 39 passed and one failure in the Chromium-clock copy-dialog case:
`document.activeElement === document.body` was false immediately after
Escape. Sorting was not reached in that full run. The independent focused
sorting results remain green; the dialog readiness failure is addressed next. The failed recording remains available alongside the
earlier complete green qualification at `47cb64da`.

## Dialog dismissal and focus

The pre-merge full native qualification found a separate failure after
39 passes: `test_copy_menu_refusal_dialog[Copy absolute path-1-1000]` saw
`document.activeElement === document.body` false immediately after Escape.
The dialog was already hidden. This case uses the existing Chromium-clock
fixture even under the native command. Forty-three later cases were
unreported. The compound qualification exited 1 after 195.4 s.

[The manual-copy decision] requires focus return after dismissal. Visibility
and browser focus restoration are separate readiness states. The test now
resumes its clock after all timed copy assertions, dismisses the dialog, and
waits for both hidden state and restored body focus. Both original assertions
remain, with the case's existing 3,000 ms readiness bound. Application dialog
behavior and the approved focus policy are unchanged.

All six menu/width variants passed in bundle mode (19.90 s) and all six
passed in development mode (15.69 s). Complete native qualification then passed all 83 cases in 575.36 s.
The compound command, including every quality hook, explicit Python checks
and 32 documentation/readiness/partition cases, passed in 600.2 s. Both
readiness repairs are qualified before merging.

## Real layout around controlled clock phases

At `f0c0b9ee`, native build and 20 contracts passed. The native UI command
then stopped with eight passed and one failure in the pending-rebase probe's
final positive assertion: `The completed rebase can settle` observed false.
Pytest time was 29.72 s; guarded wall time was 37.0 s. The negative held-timer
assertion had passed. Seventy-four UI cases and later queued commands were
unreported in this round.

The positive phase still advanced fixed virtual time around real CSS motion.
The shared clock fixture now waits for preview eligibility and real dial
settlement before pausing time. After the controlled held-timer phase, the
probe resumes its clock and uses the existing 6,000 ms settlement helper to
observe actual browser geometry. Its original negative and positive assertions
remain. The helper's bound and production scrolling behavior are unchanged.

Eight controlled rebase, fling and dialog cases passed in bundle mode
(35.69 s) and the same eight passed in development mode (38.98 s). Full native
qualification then passed all 83 cases in 617.28 s. The compound command
including all quality hooks, explicit Python checks and 32 focused cases
passed in 642.5 s before merging.

## Server tap readiness

At `14cb7d3b`, native build, 20 native contracts, 83 native UI cases,
83 static UI cases, 193 development cases and 110 static adapter cases
passed. The keyboard shard stopped with 65 passed and one failure in
`test_status_bar_items_stay_on_one_line_when_hints_do_not_fit[viewport1]`:
`_ui_tap` reached its unchanged 30,000 ms selection/path wait after the
wide-chain input failed to select its target. Pytest time was 344.78 s;
guarded wall time was 346.6 s. One keyboard case and later queued commands
were unreported.

The server keyboard dial helper still used the older geometry-only predicate.
It now checks pending dial work as well, using the same debug surface as the
controlled regression. After a spine is unfolded, the input helper waits for
settlement before clicking its row. The served UI module's duplicate dial
predicate is aligned too. All geometry, selection, status-bar and clipping
assertions remain; the 6,000 ms settlement bound is unchanged. Browser/server
lifecycle and parallel qualification owned by [fixture isolation] are untouched.

The three status-bar viewport cases and both mobile wide-folder cases passed
(5 in 51.76 s). Complete keyboard qualification then passed: 67 passed in 326.27s (0:05:26).
The related served folding/navigation checks passed: 6 passed in 54.86s.
All quality hooks and 32 focused checks passed. The compound command took
388.7 s before merging the input-readiness repair.

## Preserve cached column geometry

The fifteenth merged-main recording completed all twelve checks. Eleven
passed: all six root shards (1,501 cases), development (193), native build,
native contracts (20), exact collection coverage and the quality gate.
Native UI finished with 82 passed and one failure: `test_render_cost`
measured a 3,000-entry re-render at 112 ms against its unchanged 100 ms
budget; the keystroke measurement passed at 18.7 ms. Its complete log and
JUnit file remain in [the run directory]. No hardware exception applies.

Inspection found that [the renderer] replaced each cached column's entire
class attribute before layout. This stripped layout-owned `folding`,
`spine` and overflow classes, invalidating settled geometry before layout
restored it. A deterministic assertion added to [the cached-render regression][cached-render regression]
observes column class mutations during an unchanged render: red reported
four writes, whereas green reports zero. The renderer now toggles only its
four owned state classes and preserves layout's classes. The original timing
assertions and their 100 ms budgets remain unchanged. The existing no-repeat-sort
assertion is preserved too. Both focused development cases passed in 10.20 s.
A first native probe still used the previously built binary and correctly
reported the old four class writes (one failed, one passed). Rebuilding with
the guide's command made both native cases pass in 36.83 s. The quality gate
then rejected the stale checked-in static bundle; an initial regeneration
command used the wrong script location and exited 2 before building. The
correct [static build script] regenerates that artifact in this commit.
Final merged-main qualification follows below.


[144]: 144-make-the-full-static-suites-pass-reliably-the-wide-folder-wait-and-tes.md
[fixture isolation]: 141-finish-browser-fixture-isolation-and-qualify-independent-test-roots.md
[the baseline log]: http://hopeli/tmp/filemill-hai156/baseline-root.log?f
[the memory log]: http://hopeli/tmp/filemill-hai156/memory.jsonl?f
[the run directory]: http://hopeli/tmp/filemill-hai156/?f
[The evidence receipt]: 156-make-filemill-s-root-suite-finish-green-within-its-30-minute-bound-on-.evidence.json
[the first failed receipt]: http://hopeli/tmp/filemill-hai156/receipt-981e4d53-failed.json?f
[second failed receipt]: http://hopeli/tmp/filemill-hai156/receipt-f4210f8a-failed.json?f
[native guide]: ../../native/README.md#checks
[third failed receipt]: http://hopeli/tmp/filemill-hai156/receipt-c83e31bd-failed.json?f
[static reliability]: 144-make-the-full-static-suites-pass-reliably-the-wide-folder-wait-and-tes.md
[the architecture-summary task]: 157-point-agents-at-a-short-summary-of-the-architecture-review-instead-of-.md
[the manual-copy decision]: 119-document-the-menu-copy-exception-from-docs-question-4.md
[the renderer]: ../../server/src/filemill/ui/core/render.js
[cached-render regression]: ../../static/tests/test_ui.py
[static build script]: ../../static/build-index.py
[the issue description]: 156-make-filemill-s-root-suite-finish-green-within-its-30-minute-bound-on-.md
