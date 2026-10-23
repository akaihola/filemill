Steward issue, 2026-10-21 14:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 2 h. Source: the steward's triage of the review queue, `<steward-vault>/notes/2026-10-21-left-to-antti-triage.md`.


Two finished items wait in the review queue for the same reason: the server keyboard helper still starts its own browser lifecycle, and the application-local test roots were never qualified by a parallel whole-suite run. Triage section "Prepare the specific repairs", items "Shared Filemill browser fixtures" and "Independent Filemill test roots" (the unnumbered entries in `TASKS.md`).

## Work

1. Move the server keyboard helper onto the shared browser fixture, removing the duplicate lifecycle. Keep every existing browser assertion.
2. Run the documented parallel test command with the application roots isolated, and declare any dependency it needs.
3. Before claiming the original change is preserved or reversible, find its implementation boundary in the history and name the commits.

## Acceptance

- The documented parallel command passes with fixtures isolated, and no test starts its own browser.
- The commits of the original change and of this one are named in the task file.
- The parallel run is the heaviest command here: if hopeli can't hold it under the memory rule, record the readings and stop instead of lowering the bar. Memory: follow your launch prompt's memory rule, and run one heavy command (test suite, browser, build) at a time.


## Implementation record — 2026-10-21

The original implementation boundaries were inspected in Git:

- `b02a3ad5` (`fix(server): isolate configured test root`) replaced temporary
  mutation of the module-global default root with application-state root
  configuration and monkeypatch restoration. The application retains a default
  root for direct ASGI loading. This was not an application-factory change.
- `6390cdc0` (`test: unify browser test fixtures`) moved server fixtures into
  [the root fixtures] and introduced shared synchronous and asynchronous
  Playwright entry points. The keyboard helper still opened its own driver.
- `587752b4` (`test(static): migrate browser checks to pytest`) migrated the
  static suite and established the shared uv workspace. It retained several
  launches inside individual static tests.

These changes have separate boundaries; reverting one is not evidence that
reverting all three together is safe. No revert was performed.

### Repair and validation plan

- Add a failing source guard for browser lifecycle calls outside fixtures.
- Move the keyboard helper and direct test launches onto fixture-owned
  browsers. Keep the persistent storage profile in a dedicated fixture.
- Preserve existing assertions and application-state root restoration.
- Declare pytest-xdist in both development dependency groups and update the
  shared lock. Document root `uv run pytest -n auto` in [the contribution guide].
- Run that exact whole-suite command with memory admission, monitoring and
  process-group cleanup. A resource stop or test failure leaves acceptance open.

The [lifecycle guard] failed before the migration. Afterwards, it and the pytest
configuration checks passed: 11 tests in 3.07 seconds. All 783 existing assertion
ASTs in the migrated modules match after normalizing string whitespace changed
by dedenting lifecycle blocks; the keyboard module retains its 113 assertions.

The repair is commit `2d77abdd` (`test: centralize browser lifetimes and declare
parallel runner`). The task plan is `461950e5`; the canonical start move is
`66572076`. The parallel qualification is blocked by the resource stop below.


## Qualification stopped — 2026-10-21

The exact documented command, `uv run pytest -n auto`, created four workers
and collected 1,433 tests. It reached the 75% progress marker. One failure
marker appeared before the stop; the run did not reach its traceback or final
summary. Its cause is unclassified. This is not a passing qualification.

The memory guard sampled the host each second. It stopped the command and
its process group when swap growth reached 513 MiB, above the 512 MiB limit.
The final readings below were taken after process cleanup; swap growth had
then fallen to 186 MiB. No captured test descendant remained alive afterwards.
The run had a one-hour timeout and was the only heavy command running here.

### Guarded commands and readings

All readings use MiB. Each command waited 0.0 seconds for admission. No command
used fallback admission. Elapsed time excludes the admission wait.

- **Red:** `uv run --project server pytest server/tests/test_browser_lifecycle.py -q`
- **Green:** `uv run --project server pytest server/tests/test_browser_lifecycle.py server/tests/test_pytest_config.py -q`
- **Parallel:** `uv run pytest -n auto`

| Command | Outcome | MemAvailable admission / final | Starting swap | Swap growth final / peak | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Red | started at once | 3282 / 3246 | 2190 | -1 / 0 | 5.0 s | exit 1, expected red |
| Green | started at once | 3245 / 3164 | 2188 | 0 / 0 | 4.0 s | exit 0 |
| Parallel | stopped while running | 3253 / 3331 | 2187 | 186 / 513 | 914.8 s | stopped |

### Remaining acceptance

The source guard and configuration checks passed before the full run. The
changed Python files passed Ruff lint and formatting checks. Existing browser
assertions remain in place, and the original and repair commits are named
above. Application code and the existing root-restoration mechanism did not
change.

The whole parallel suite has not passed. Its observed failure still needs a
traceback and investigation. In accordance with the memory rule, no smaller
worker run, further browser suite, full pre-commit gate, or build was started
after the stop. The static development suite is also unverified.

The repair commits remain on the worktree branch. Do not merge, deploy, or move
this issue to Completed / Accepted on this evidence. The canonical tracker
remains In Progress, with no acceptance checkbox changed. Resume qualification
on a host that can hold the same command under the required limits.




## Resumed qualification — 2026-10-23

The steward's follow-up replaces aggregate parallel qualification with the
six sequential root shards from [the bounded-suite work][156] and
[the testing commands]. The earlier stop record remains historical evidence;
it does not block completion on the new results below. This record does not
claim a new `-n auto` pass.

The prerequisite was checked in local main `6f7818b0`: the bounded-suite task
was in Completed / Accepted with acceptance unchecked. The branch was then
rebased onto that commit. The conflicts were documentation-only: retain the
new shard commands in the contribution guide and retain both sets of
architecture references. No test-root code conflict required a scope decision.
The rebased implementation boundary is `1a35b016`, from original `2d77abdd`.
The original changes remain `b02a3ad5`, `6390cdc0` and `587752b4`, as recorded
above. The rebased pre-qualification tip is `f0ed92f3f7fc4a20c380cc10e841755a8dfedf14`.

### Historical failure identity

The old stopped log contains only a failure marker. It has no test ID or
traceback, and the pytest last-failed cache is empty. The failure could not be
recovered or rerun individually. No test name was inferred from the position
of a marker in interleaved worker output. This is an evidence gap in the old
run, not an identified regression.

Every current root case was rerun in the six complete shards. All 1,502 cases
passed without skips. Both served halves ran, with complementary deselections.
The collection comparison proved exact ID multiplicity between the root suite
and the six shards. The extra case over main's 1,501 is the lifecycle guard.
The static development suite also passed all 193 cases. The quality gate
passed all seven hooks and the DOM-free model checks.

### Check results

All checks below ran on clean checkout `f0ed92f3f7fc4a20c380cc10e841755a8dfedf14` with the same lockfile.
The receipt records exact arguments, timestamps, input hashes, result files
and log hashes. Pytest commands retain the documented 1,800-second timeout;
reporting flags add quiet output, short tracebacks and JUnit files.

| Check | Passed cases or result | Guarded elapsed seconds |
| --- | --- | ---: |
| keyboard | 67 | 334.5 |
| served-ui-early | 157 | 314.8 |
| served-ui-late | 156 | 391.1 |
| server-contracts | 929 | 21.4 |
| static-ui | 83 | 308.1 |
| static-adapters | 110 | 248.6 |
| collections | 1,502 IDs equal | 11.3 |
| static-dev | 193 | 599.9 |
| quality | hooks + model passed | 14.4 |
| docs | 28 | 3.1 |

### Memory readings

Each check ran alone, with one-second host memory monitoring and process-tree
cleanup. All admission waits were 0.0 seconds. No fallback admission, resource
stop or retry was required. Readings use MiB; swap growth is relative to the
start of each command. This table contains resource readings and exit status,
not command output. Exact command vectors are in [the check receipt].

| Command | Outcome | Wait s | MemAvailable admission / final | Swap start / growth | Peak growth | Elapsed s | Exit |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: |
| keyboard | started at once | 0.0 | 3011 / 2785 | 2343 / +10 | 10 | 334.5 | 0 |
| served-ui-early | started at once | 0.0 | 2823 / 2877 | 2353 / +18 | 19 | 314.8 | 0 |
| served-ui-late | started at once | 0.0 | 2886 / 2918 | 2371 / +35 | 36 | 391.1 | 0 |
| server-contracts | started at once | 0.0 | 2936 / 2814 | 2406 / +0 | 0 | 21.4 | 0 |
| static-ui | started at once | 0.0 | 2874 / 2895 | 2401 / +19 | 21 | 308.1 | 0 |
| static-adapters | started at once | 0.0 | 3097 / 2801 | 2418 / -61 | 3 | 248.6 | 0 |
| collections | started at once | 0.0 | 2874 / 2736 | 2357 / -1 | 0 | 11.3 | 0 |
| static-dev | started at once | 0.0 | 2893 / 2948 | 2355 / -4 | 26 | 599.9 | 0 |
| quality | started at once | 0.0 | 3246 / 3092 | 2350 / -1 | 0 | 14.4 | 0 |
| docs | started at once | 0.0 | 3063 / 3031 | 2347 / +0 | 0 | 3.1 | 0 |

### Delivery and completion

Application code and the application-state root-restoration mechanism did not
change in this issue. A comparison against the rebased main confirmed the
same assertion ASTs in every migrated file (694 assertions), allowing string
whitespace changes from dedenting lifecycle blocks. The automated root tests
retain fixture-owned browser lifetimes, guarded by [the lifecycle guard].

The clean qualification is complete. The repair and report were merged
locally into main at `77177d7a`. The tracker moved to Completed / Accepted
with acceptance unchecked. The completion commit includes [the check receipt].
The final documentation check passed 28 tests on clean report commit
`77177d7a`; the receipt distinguishes it from the code qualification commit.
No restart or deployment was performed. [The run artifacts] retain the logs,
JUnit files, collection lists and per-command memory records.

[the root fixtures]: ../../conftest.py
[the contribution guide]: ../../CONTRIBUTING.md
[lifecycle guard]: ../../server/tests/test_browser_lifecycle.py
[156]: 156-make-filemill-s-root-suite-finish-green-within-its-30-minute-bound-on-.md
[the testing commands]: ../../CONTRIBUTING.md#tests
[the check receipt]: 141-finish-browser-fixture-isolation-and-qualify-independent-test-roots.evidence.json
[the lifecycle guard]: ../../server/tests/test_browser_lifecycle.py
[The run artifacts]: http://hopeli/tmp/filemill-hai141-resume/?f
