---
depends-on: [120]
---

# Give served and browser-owned folders the same content search

Source: [the documentation review], question 5.
User review, 2026-10-20. Label: `steward`.

## Decision

Approved direction: the search control, results and interaction should be identical for served content and browser-owned folders. The [temporary hiding fix] remains necessary until this capability is implemented.

## Work

1. Use one shared search UI with equivalent query behavior, focused-folder scope, result presentation, keyboard activation, cancellation and empty/error states.

2. Put the search operation behind an adapter capability. The server uses its content search and the browser reads only its granted folder; local search must not upload file contents or call the server's search endpoint.

3. Bound traversal, reads and returned matches, and indicate partial results. Invalidate pending searches when the root or query changes. Open local results through navigation without requiring a URL router.

4. Start with failing browser checks for both sources and mode transitions. Document the capability and any measured limits in the behavior ADR.

## Acceptance

Equivalent fixtures produce equivalent visible results and interactions in both modes. Tests show no server search request for a browser-owned folder and no stale results after switching roots. The search control is restored in local mode once it has real local functionality.

## Implementation plan

- Add browser regressions for the same literal query, first matching line,
  focused directory, empty/error states and keyboard activation in both modes.
- Give each filesystem an optional search capability. Bind it to the mounted
  root. Clear pending work on query and root changes. Use shared navigation
  for result activation, including mounts without a router.
- Bound folder traversal and byte reads. Show partial results at a limit.
  Exercise delayed reads and transitions between local and served roots.
- Record the behavior and limits in an ADR. Rebuild the static bundle, run
  the quality gate and each browser edition, then merge and complete the task.

## Implementation, 2026-10-22

The filesystem now supplies optional `search(root, query, focused, signal)`.
Mounting binds it to the current root. The HTTP adapter owns its endpoint;
the browser adapter reads only granted handles. Shared result activation uses
navigation with an optional router. Query changes invalidate pending work
immediately, including during the debounce delay.

[The behavior decision] records the query contract, limits, errors and
cancellation boundaries. [The usage guide] and [the adapter guide] describe the
restored control. Architecture findings A10 and A12 now distinguish bounded
search acquisition from the remaining acquisition and async ownership work.

The browser capability checks observed 2,000 enumerated entries, 16 reads of
1 MiB files, 100 matching files and no match below the depth limit. Oversized
files are skipped before byte reads. These are deterministic fixture counts,
not disk throughput measurements.

## Validation record

- **Initial red:** browser transition checks failed because local search was
  hidden. The equivalent-fixture check also exposed an incorrect test focus
  assumption; the test now focuses a row in the child column explicitly.
- **Server red:** new oversized-file and traversal-limit checks failed because
  the server returned unbounded matches without a partial flag.
- **Static red:** the new static activation check failed against the old
  bundle because its search control had been removed.
- **Focused green:** eight initial parity/transition checks and thirteen server
  search/policy checks passed. Nine extended browser checks passed for local
  late reads, partial notices and resource bounds.
- **Fixture correction:** the first extended run had three wait timeouts.
  Playwright invoked the function returned by its wait expression. The wait
  now checks the callback's type without invoking it; all six delayed local
  success/error transition cases then passed.
- **Initial gate:** only the Markdown formatter failed. The adapter guide was
  formatted. Ruff, Python format, mypy, Deno lint, suppression links and bundle
  consistency passed in that run. Model checks also passed.

- **First full bundle:** 187 passed; the new activation test failed because it
  searched a root containing deliberate permission-denied fixtures. The test
  now focuses the readable Python fixture folder. No product error was hidden.
- **Additional parity red:** explicit hidden-folder scope and astral-character
  context length failed in local mode (two failures, four passes). Local scope
  resolution now includes explicitly named hidden folders; root-wide traversal
  still skips hidden entries. Context clipping now counts Unicode code points
  in both implementations. UTF-8 BOM fixtures already agreed.

- **Full server:** 1,292 passed in 1,548.86 seconds. No server checks failed
  or were skipped. The complete quality gate passed after formatting.
- **Frozen search checks:** all 30 browser search checks passed, including
  focused hidden folders, astral Unicode and UTF-8 BOM fixtures. The rebuilt
  bundle activation check passed in isolation before the full rerun.

- **Full static bundle:** 188 passed in 1,226.68 seconds. This complete rerun
  verifies the corrected fixture and the final runtime code.
- **Full static development:** 188 passed in 667.89 seconds. Both static runs
  reported two Docutils deprecation warnings and no failures or skips.
- **Native checks:** the first contract invocation failed all 19 checks because
  this worktree had no built host. The documented native build succeeded;
  the rerun passed all 19 contracts. The native capability smoke check also
  passed and confirms that a filesystem without search keeps the control
  hidden. The full native UI suite was not rerun; native content search is
  outside this issue.
- **Documentation and gate:** all 27 documentation checks passed after the
  final wording changes. The quality gate and shared model checks passed.

## Merge record

Implementation commit `2c81aced` was merged into local `main` as `93338839`
on 2026-10-22. Rebase incorporated only new tracker and task documentation;
runtime and test sources match the validated working tree. The feature branch
is retained. No push, service restart or deployment was performed.

Implementation and validation are complete. The completion move leaves the
acceptance checkbox unchecked for steward review.

## Resource guard

All runs used sequential admission and runtime monitoring. MemAvailable and
swap figures are MiB. Each command had a 1,800-second execution timeout.
No command was stopped by the memory guard.

- **Run 1: started at once.** `uv run --project server pytest -q server/tests/test_browser_new_ui.py -k 'shared_content_search or local_mode_cancels' --maxfail=2`; wait 0.0 s; MemAvailable 2762 → 2754; swap start 2402, growth +10; elapsed 25.0 s; exit 1.
- **Run 2: started at once.** `uv run --project server pytest -q server/tests/test_browser_new_ui.py -k shared_content_search --maxfail=2`; wait 0.0 s; MemAvailable 2816 → 2824; swap start 2411, growth +3; elapsed 19.1 s; exit 1.
- **Run 3: started at once.** `uv run --project server pytest -q server/tests/test_browser_new_ui.py -k 'shared_content_search or local_mode_cancels' --maxfail=2`; wait 0.0 s; MemAvailable 2904 → 2693; swap start 2451, growth -3; elapsed 34.1 s; exit 0.
- **Run 4: started at once.** `uv run --project server pytest -q server/tests/test_api.py -k 'search_reports_partial or search_bounds_traversal'`; wait 0.0 s; MemAvailable 2734 → 2660; swap start 2448, growth +0; elapsed 5.0 s; exit 1.
- **Run 5: started at once.** `uv run --project server pytest -q server/tests/test_api.py server/tests/test_public_mode.py -k search`; wait 0.0 s; MemAvailable 2784 → 2769; swap start 2446, growth +0; elapsed 4.0 s; exit 0.
- **Run 6: started at once.** `uv run --project server pytest -q server/tests/test_browser_new_ui.py -k search --maxfail=3`; wait 0.0 s; MemAvailable 2687 → 2714; swap start 2444, growth -13; elapsed 166.3 s; exit 1.
- **Run 7: started at once.** `uv run --project server pytest -q server/tests/test_browser_new_ui.py -k 'local_search or shared_search_reports' --maxfail=2`; wait 0.0 s; MemAvailable 2702 → 2746; swap start 2431, growth -22; elapsed 33.1 s; exit 0.
- **Run 8: started at once.** `uv run pytest -q static/tests/test_ui.py -k content_search --bundle`; wait 0.0 s; MemAvailable 2808 → 2638; swap start 2408, growth +0; elapsed 4.0 s; exit 1.
- **Run 9: started at once.** `python3 static/build-index.py`; wait 0.0 s; MemAvailable 2651 → 2659; swap start 2407, growth +0; elapsed 1.1 s; exit 0.
- **Run 10: started at once.** `uvx pre-commit run --all-files`; wait 0.0 s; MemAvailable 2502 → 2786; swap start 2406, growth +0; elapsed 26.0 s; exit 1.
- **Run 11: started at once.** `uv run pytest static/tests --bundle -q`; wait 0.0 s; MemAvailable 2847 → 2655; swap start 2405, growth -13; elapsed 780.9 s; exit 1.
- **Run 12: started at once.** `uv run --project server pytest -q server/tests/test_browser_new_ui.py -k 'search_can_focus or search_context_is'`; wait 0.0 s; MemAvailable 2862 → 2657; swap start 2391, growth +10; elapsed 27.1 s; exit 1.
- **Run 13: started at once.** `uv run --project server pytest -q server/tests/test_browser_new_ui.py -k search --maxfail=2`; wait 0.0 s; MemAvailable 2571 → 2755; swap start 2400, growth +76; elapsed 99.2 s; exit 0.
- **Run 14: started at once.** `python3 static/build-index.py`; wait 0.0 s; MemAvailable 2709 → 2687; swap start 2475, growth +0; elapsed 1.0 s; exit 0.
- **Run 15: started at once.** `uv run pytest -q static/tests/test_ui.py -k content_search --bundle`; wait 0.0 s; MemAvailable 2718 → 2757; swap start 2475, growth +1; elapsed 7.0 s; exit 0.
- **Run 16: started at once.** `uvx pre-commit run --all-files`; wait 0.0 s; MemAvailable 2837 → 2620; swap start 2475, growth +4; elapsed 9.0 s; exit 0.
- **Run 17: started at once.** `uv run --project server pytest server/tests -q`; wait 0.0 s; MemAvailable 2671 → 2644; swap start 2483, growth -111; elapsed 1552.8 s; exit 0.
- **Run 18: started at once.** `uv run pytest static/tests --bundle -q`; wait 0.0 s; MemAvailable 2714 → 2721; swap start 2363, growth -33; elapsed 1230.1 s; exit 0.
- **Run 19: started at once.** `uv run pytest static/tests --dev -q`; wait 0.0 s; MemAvailable 2823 → 2810; swap start 2324, growth -11; elapsed 670.5 s; exit 0.
- **Run 20: started at once.** `nix-shell native/shell.nix --run 'uv run --project server pytest native/test_host.py -q'`; wait 0.1 s; MemAvailable 2904 → 2790; swap start 2312, growth +3; elapsed 21.1 s; exit 1.
- **Run 21: started at once.** `nix-shell native/shell.nix --run 'python3 native/webview/build.py'`; wait 0.0 s; MemAvailable 2645 → 2779; swap start 2314, growth +2; elapsed 12.1 s; exit 0.
- **Run 22: started at once.** `nix-shell native/shell.nix --run 'uv run --project server pytest native/test_host.py -q'`; wait 0.0 s; MemAvailable 2905 → 2918; swap start 2316, growth +52; elapsed 43.1 s; exit 0.
- **Run 23: started at once.** `nix-shell native/shell.nix --run 'uv run --project server pytest static/tests/test_ui.py --native -q -k content_search'`; wait 0.0 s; MemAvailable 2909 → 2889; swap start 2367, growth +5; elapsed 13.0 s; exit 0.
- **Run 24: started at once.** `uv run --project server pytest -q server/tests/test_docs.py`; wait 0.0 s; MemAvailable 2926 → 2920; swap start 2372, growth +0; elapsed 3.0 s; exit 0.
- **Run 25: started at once.** `uvx pre-commit run --all-files`; wait 0.0 s; MemAvailable 2971 → 2891; swap start 2372, growth +0; elapsed 6.0 s; exit 0.

[The behavior decision]: ../adr/0092-shared-content-search-capability.md
[The usage guide]: ../USAGE.md#content-search
[The adapter guide]: ../../server/src/filemill/ui/adapters/README.md

[the documentation review]: 109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions
[temporary hiding fix]: 120-disable-server-search-in-local-folders-from-docs-question-5.md
