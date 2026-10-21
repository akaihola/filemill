Steward issue, 2026-10-21 17:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 2 h.


Two intermittent failures keep filemill's full static suites from being a reliable gate, and they hold finished work:

- **Wide-folder wait.** The steward's browser evidence packet (`<steward-vault>/agents/steward/log/2026-10-21-filemill-browser-evidence.md`, vault [76]) found the full static development suite timing out at the wide-folder path/kids wait, before the clipping assertions, in two fresh runs (items "Historical red-test fixes" and "Static UI runs through editor checks"). Narrower UI runs passed. The cause is not established.
- **test_rst release count.** [120]'s daytime gate (its task file, "Daytime gate, 2026-10-21") saw the static bundle's `test_rst` expect one Python global-scope release after a failed RST conversion and observe two (`window.__pyStats.destroyed` was 2). The same test passed in 11 isolated runs on unchanged `main` and in the development build. The suite stopped at that first failure, so the rest of the bundle suite did not run.

## Work

1. Reproduce each under the full suite, not only in isolation: ordering, shared browser state, timing under load and leftover Pyodide state are the first suspects. Record the runs and the rate.
2. Fix the cause in the test or the code, whichever is wrong. If a wait is a guess of readiness, replace it with an observable condition (see the waiting guidance [122] added).
3. If a cause can't be found within the estimate, record what was ruled out and the reproduction rate, and say so; don't loosen an assertion to make it pass.

## Acceptance

- The full static development suite and the full static bundle suite each pass three times in a row, run one at a time.
- The task file records the cause of each failure, or the evidence that rules causes out.
- [141]'s fixture isolation work is not duplicated; if the cause lies there, link it and say so.

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
