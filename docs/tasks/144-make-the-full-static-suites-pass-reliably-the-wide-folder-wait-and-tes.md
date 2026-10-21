Steward issue, 2026-10-21 17:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 2 h.


Two intermittent failures keep filemill's full static suites from being a reliable gate, and they hold finished work:

- **Wide-folder wait.** The steward's browser evidence packet (`<steward-vault>/agents/steward/log/2026-10-21-filemill-browser-evidence.md`, vault [76]) found the full static development suite timing out at the wide-folder path/kids wait, before the clipping assertions, in two fresh runs (items "Historical red-test fixes" and "Static UI runs through editor checks"). Narrower UI runs passed. The cause is not established.
- **test_rst release count.** [the server-search task]'s daytime gate ("Daytime gate, 2026-10-21") saw the static bundle's `test_rst` expect one Python global-scope release after a failed RST conversion and observe two (`window.__pyStats.destroyed` was 2). The same test passed in 11 isolated runs on unchanged `main` and in the development build. The suite stopped at that first failure, so the rest of the bundle suite did not run.

## Work

1. Reproduce each under the full suite, not only in isolation: ordering, shared browser state, timing under load and leftover Pyodide state are the first suspects. Record the runs and the rate.
2. Fix the cause in the test or the code, whichever is wrong. If a wait is a guess of readiness, replace it with an observable condition (see [the waiting guidance]).
3. If a cause can't be found within the estimate, record what was ruled out and the reproduction rate, and say so; don't loosen an assertion to make it pass.

## Acceptance

- The full static development suite and the full static bundle suite each pass three times in a row, run one at a time.
- The task file records the cause of each failure, or the evidence that rules causes out.
- [Fixture isolation] work is not duplicated; if the cause lies there, link it and say so.

- Your completion message lists the tests added and the checks run.
- No push, deployment, live service, real account or credential. Memory: follow your launch prompt's memory rule, and run one heavy command (test suite, browser, build) at a time.

## Investigation plan, 2026-10-21

1. Run each complete static suite sequentially and record failures and memory.
2. Trace the wide-folder selection and RST conversion lifetime. Add controlled
   regressions before changing either implementation or test readiness.
3. Keep [fixture isolation] outside this change. Preserve clipping and exact
   Python-global release assertions.
4. Run both full suites three consecutive times each, then the required lint
   and bundle checks. Record causes, reproduction counts and limitations here.


## Controlled RST regression, 2026-10-21

The new `test_rst_failure_releases_one_scope_during_layout` in
[the rich-preview tests] holds a conversion on an explicit promise, observes
its start, resizes the page and requests another render, then releases a
conversion failure. It checks one conversion, one released Python scope,
the same preview pane and readable source fallback. The existing exact
release-count assertions remain unchanged.

These renders have real callers: [the static bootstrap] renders again when
fonts become ready, and [the layout handler] renders on resize. The explicit
second render models the fonts-ready callback. Holding the conversion through
both renders establishes overlap without a guessed time window.

- **Red:** temporarily restoring the preview implementation immediately before
  `9b66ee7c` produced three conversions and three releases for one selection.
  The interpreter boot and package load each happened once. Each layout render
  started another conversion, each releasing its own scope. The historical
  implementation was restored only for this controlled
  development test, then replaced with the current implementation immediately.
- **Green:** current main's preview implementation passed the same check with
  exactly one conversion and release. [The preview reuse repair] already owns
  the production correction (`9b66ee7c`, `c8c22937`). This task adds the RST
  lifetime regression.
- **Limit:** this reproduces a mechanism that explains excess releases. Without
  a trace from the original daytime failure, it does not establish which
  render event caused that specific second conversion.


## Wide-folder investigation, 2026-10-21

The retained [development failure log] identifies the wait inside the nested
long-folder walk in `test_folding_dial`, after a click, rather than the initial
selection of `wide`. That predicate already observes the expected path depth
and loaded children. It is not a fixed readiness sleep. Data readiness does
not establish that layout motion has stopped; that remains a candidate if
this failure returns.

The baseline development run passed all 184 checks. The following bundle run
added temporary pointer-down, pointer-up and click logging with the selected
names, open path, focus, fold count, dial and stage scroll. This instrumentation
preserved input and readiness. It was removed before final qualification.

- **Cross-test browser state:** the existing static fixture creates a fresh
  browser for each test. Origin-backed tests also receive a fresh loopback
  port. This rules out carrying a JavaScript interpreter or browser globals
  from a previous test in these runs. It does not rule out overlap within a
  test, or host-load effects.
- **Within-test remounts:** the full suites retain the existing remount and
  pending-preview regressions. No fixture lifecycle is changed; [fixture
  isolation] remains separate work.
- **Remaining uncertainty:** no trace of the historical missed transition was
  retained with its pointer targets or model state. A passing current run
  cannot establish its cause or rule out all ordering and timing effects.
  Existing assertions and timeouts are retained.


## Baseline results

Both complete suites ran sequentially on current main's production code.

| Mode | Checks | Result | Runtime |
| --- | ---: | --- | ---: |
| Development | 184 | Passed | 582.19 s |
| Bundle, including the new RST check | 185 | Passed | 975.37 s |

Neither original failure reproduced: 0/2 complete runs for each symptom.
The instrumented folding-dial test also passed. No evidence supports changing
its loaded-path predicate or relaxing its clipping assertions. The original
wide-folder cause remains unestablished. Final qualification repeats follow
below; these baseline passes alone are not the acceptance gate.

## Final qualification, 2026-10-21

The final regression and production code passed three consecutive complete
suites in each mode. All six runs were sequential.

| Run | Checks | Result | Pytest runtime |
| --- | ---: | --- | ---: |
| Development 1 | 185 | Passed | 1,251.35 s |
| Development 2 | 185 | Passed | 848.73 s |
| Development 3 | 185 | Passed | 797.23 s |
| Bundle 1 | 185 | Passed | 686.59 s |
| Bundle 2 | 185 | Passed | 699.74 s |
| Bundle 3 | 185 | Passed | 679.51 s |

Across both baselines and these six repeats, neither original failure
reproduced: **0/8 full-suite runs for each symptom**. The new controlled RST
regression passed in every final run. Its historical red probe failed 1/1,
with three conversions/releases, while the current focused green probe passed
1/1 with one conversion/release.

The RST duplication mechanism is guarded by the new test and already corrected
by [the preview reuse repair]. The original wide-folder cause remains
unestablished. Fresh browsers rule out cross-test JavaScript globals in these
runs; within-test ordering, asynchronous layout and host-load effects remain
possible. Existing waits, clipping checks and release-count assertions are
retained. [Fixture isolation] implementation remains separate work.

Final validation passed after rebasing on main: all 28 documentation/wait
checks, the model checks, explicit Ruff and format checks for [the rich-preview
tests], and all seven pre-commit checks. These cover Python lint/format/types,
UI lint/format, suppression links and generated-bundle consistency. The diff
has no whitespace errors.

The rebase preserved main's intervening tracker, documentation and served
browser-regression changes. The shared UI, static edition and pytest
configuration are identical to the qualified files. The architecture review
records the new lifetime regression alongside the existing preview repair.

## Memory guard evidence

Host readings are MiB. Admission waits at most 600 seconds for 2,048 MiB;
the fallback requires 1,536 MiB. Each command has a 1,800-second runtime limit.
The monitor stops the command and its children below 1,024 MiB available or
above 512 MiB swap growth. All commands ran sequentially. No command required
the fallback or a memory stop.

Command keys:

- **D:** `uv run --project server pytest static/tests --dev -q`
- **R:** `uv run --project server pytest static/tests/test_rich.py --dev -q -k test_rst_failure_releases_one_scope_during_layout`
- **B:** `uv run --project server pytest static/tests --bundle -q`
- **M:** `node ui/core/model/test.mjs`
- **W:** `uv run --project server pytest -q server/tests/test_docs.py server/tests/test_browser_waits.py`
- **P:** `uvx pre-commit run --all-files`

The R historical red exit is the expected failing regression probe. Elapsed
time covers the guarded command, separately from its admission wait. Command
outputs are retained in [the run logs]; this table contains memory and status
metadata only. [The machine-readable readings] also retain peak swap growth.

| Command and run | Outcome | Wait s | Available in / out | Swap start / growth | Elapsed s | Exit |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| D: baseline-dev | started at once | 0.0 | 3255 / 3212 | 2451 / -46 | 586.2 | 0 |
| R: rst-historical-red | started at once | 0.0 | 3309 / 3171 | 2405 / +0 | 4.0 | 1 |
| R: rst-current-green | started at once | 0.0 | 3156 / 2990 | 2404 / +0 | 5.1 | 0 |
| B: baseline-bundle | started at once | 0.0 | 2889 / 2555 | 2403 / +120 | 984.1 | 0 |
| D: final-dev-1 | started at once | 0.0 | 2722 / 2629 | 2516 / -188 | 1255.2 | 0 |
| D: final-dev-2 | started at once | 0.0 | 2628 / 2975 | 2328 / +8 | 850.7 | 0 |
| D: final-dev-3 | started at once | 0.0 | 2988 / 2755 | 2330 / -49 | 799.1 | 0 |
| B: final-bundle-1 | started at once | 0.0 | 2755 / 3117 | 2281 / -73 | 688.6 | 0 |
| B: final-bundle-2 | started at once | 0.0 | 3110 / 2721 | 2202 / -29 | 701.6 | 0 |
| B: final-bundle-3 | started at once | 0.0 | 2725 / 3207 | 2173 / +117 | 680.6 | 0 |
| M: models | started at once | 0.0 | 3268 / 3274 | 2277 / +0 | 1.0 | 0 |
| W: docs-waits | started at once | 0.0 | 3274 / 3274 | 2277 / +0 | 3.0 | 0 |
| P: precommit | started at once | 0.0 | 3275 / 3179 | 2277 / +0 | 17.0 | 0 |

[fixture isolation]: 141-finish-browser-fixture-isolation-and-qualify-independent-test-roots.md
[the rich-preview tests]: ../../static/tests/test_rich.py
[The preview reuse repair]: 140-reuse-the-preview-element-across-resizes-and-folding.md
[development failure log]: http://hopeli/tmp/filemill-browser-76/logs/L095-full-static-dev.log?f
[the server-search task]: 120-disable-server-search-in-local-folders-from-docs-question-5.md
[the waiting guidance]: ../../server/CONTRIBUTING.md#wait-for-an-element-never-for-a-duration
[the static bootstrap]: ../../ui/adapters/app-fsa.js
[the layout handler]: ../../ui/core/layout.js
[the run logs]: http://hopeli/tmp/filemill-hai144-20261021/?f
[the machine-readable readings]: http://hopeli/tmp/filemill-hai144-20261021/hai144-memory.jsonl?f
