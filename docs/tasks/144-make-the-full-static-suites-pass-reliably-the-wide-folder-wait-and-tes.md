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

[fixture isolation]: 141-finish-browser-fixture-isolation-and-qualify-independent-test-roots.md

## Controlled RST regression, 2026-10-21

The new `test_rst_failure_releases_one_scope_during_layout` in
[the rich-preview tests] holds a conversion on an explicit promise, observes
its start, resizes the page and requests another render, then releases a
conversion failure. It checks one conversion, one released Python scope,
the same preview pane and readable source fallback. The existing exact
release-count assertions remain unchanged.

- **Red:** temporarily restoring the preview implementation immediately before
  `9b66ee7c` produced three conversions and three releases for one selection.
  The interpreter boot and package load each happened once. Each layout render
  started another conversion; this was duplicate work, not one scope destroyed
  twice. The historical implementation was restored only for this controlled
  development test, then replaced with the current implementation immediately.
- **Green:** current main's preview implementation passed the same check with
  exactly one conversion and release. [The preview reuse repair] already owns
  the production correction (`9b66ee7c`, `c8c22937`); this task adds the RST
  lifetime regression rather than repeating that correction.
- **Limit:** this reproduces a mechanism that explains excess releases. Without
  a trace from the original daytime failure, it does not establish which
  render event caused that specific second conversion.

[the rich-preview tests]: ../../static/tests/test_rich.py
[The preview reuse repair]: 140-reuse-the-preview-element-across-resizes-and-folding.md

## Wide-folder investigation, 2026-10-21

The retained [development failure log] identifies the wait inside the nested
long-folder walk in `test_folding_dial`, after a click, rather than the initial
selection of `wide`. That predicate already observes the expected path depth
and loaded children. It is not a fixed readiness sleep. Data readiness does
not establish that layout motion has stopped; that remains a candidate if
this failure returns.

The baseline development run passed all 184 checks. The following bundle run
adds temporary pointer-down, pointer-up and click logging with the selected
names, open path, focus, fold count, dial and stage scroll. This instrumentation
changes neither input nor readiness. It is removed before final qualification.

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
  cannot establish its cause, and no assertion or timeout is loosened here.

[development failure log]: http://hopeli/tmp/filemill-browser-76/logs/L095-full-static-dev.log?f

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

[the server-search task]: 120-disable-server-search-in-local-folders-from-docs-question-5.md
[the waiting guidance]: ../../server/CONTRIBUTING.md#wait-for-an-element-never-for-a-duration
