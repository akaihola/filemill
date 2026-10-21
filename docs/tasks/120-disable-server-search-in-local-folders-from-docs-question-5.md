# Disable server search in local folders from docs question 5

Source: [109], question 5.
Proposed by [115]; approved by the user on 2026-10-20 (question 5). Label: `steward`.

## Recommendation

Hide and disable server content search whenever Open Folder mounts a browser-owned tree, then restore it on return to the served tree.

## Work

1. First add failing browser coverage for entering local mode with a pending search and visible results.
2. Clear results, cancel pending work and prevent late responses or queued input timers from querying or repopulating results in local mode. Do not leave an action that dereferences the null router.
3. Restore served-tree search on leaving local mode and record the behavior in an ADR. Keep the shared core independent of server URLs where this focused change permits; local content search remains separate work.

## Acceptance

Tests cover both transitions, no local-mode /api/search request, no stale result activation, and working served-tree search after return. The test uses delayed responses and observable state.

## User review, 2026-10-20

Approved as the immediate wrong-tree search fix. The desired shared UI and browser-owned search capability are tracked separately in [130]; hiding local search is temporary, not the product goal.

## Implementation, 2026-10-20

The server adapter supplies a search provider to the shared UI. A local mount
removes it before replacing the filesystem or router. This clears the input
and results, hides and disables search, cancels its timer and aborts its
request. Aborted requests cannot publish success or error responses. Old
result buttons cannot navigate. A served mount restores a fresh search.
See [ADR 0091].

The browser regression covers a queued input timer, delayed success and error
responses, a late response after return, and a retained result button. It
checks abort state, request counts, cleared UI and successful result navigation
after return. The first run failed because search remained visible in local mode.

## Gate follow-up, 2026-10-21

Rebased the implementation onto main `58d9d833`, including [137]. Resolved
the documentation conflicts without restoring the old architecture review.
The generated static bundle is current. All pre-commit checks and the shared
model checks passed. The rebased implementation commit is `cc32728e`.

- **Memory interruptions:** two full server attempts stopped when system swap
  grew by more than 512 MiB. Neither completed. The final attempt passed the
  earlier animation failure point and reported no test failure before the
  memory guard stopped it. No test processes remained after shutdown.
- **Server failure:** a separate attempt reported 134 passed and one failed
  in 375.30 seconds. The failure was
  `test_arrow_navigation_keeps_fold_animation_running` in [the keyboard tests].
  Its `before > during > after` assertion observed `during == after == 203`.
  The test failed in one of the two full attempts that reached it; it passed
  in the other. No assertion or implementation was changed for this failure.
- **Unchanged-main comparison:** on `58d9d833`, the same test passed in all
  20 separate isolated invocations. It also passed with the preceding keyboard
  workload and coverage enabled. That comparison was then stopped with 64
  tests passed in 767.28 seconds. The failure was not reproduced on main;
  these results do not establish it as a baseline defect.
- **Incomplete gate:** no full server attempt completed. The two full static
  suites were not rerun in this follow-up because the sequential gate did not
  get past the server suite. Earlier partial runs do not count as full passes.
- **Status:** leave this issue In Progress. Do not merge, mark it complete,
  restart a service or deploy until the full gate passes.

## Daytime gate, 2026-10-21

Rebased onto main `4d4f9900`. The merge resolution keeps [the escaping fix][139]
and search cancellation together. The search decision is now [ADR 0091];
main uses [ADR 0090] for save safety. Regenerated the static bundle. The tested
implementation commit is `93c24b4d`.

- **Repository checks:** all pre-commit hooks, shared model checks and 27
  documentation checks passed.
- **Full server suite:** 1,252 passed, three warnings, in 1,067.61 seconds.
  Branch-aware coverage is 93%. The local-search transition regressions and
  the earlier animation failure point passed.
- **Static bundle:** 80 passed and one failed in 335.77 seconds. The failure
  is `test_rst` in [the rich-preview tests], line 314. It expected one Python
  global-scope release after a failed RST conversion, but
  `window.__pyStats.destroyed` was 2. Stop-on-first-failure ended this suite.
- **Unchanged-main comparison:** the same bundle test passed in all 11
  separate isolated invocations on clean main `4d4f9900`. The failure was
  not reproduced there. These checks do not establish a baseline defect.
- **Full static development suite:** 177 passed in 615.30 seconds, including
  `test_rst`. No test assertion or RST implementation was changed.
- **Memory:** no suite hit a memory limit in this attempt. The server started
  with 2.98 GiB available, the bundle with 3.15 GiB, and development with
  3.12 GiB. Suites ran one at a time under the requested memory guard.
- **Status:** the bundle failure keeps the gate red. Leave this issue
  In Progress, with no merge, completion, acceptance, restart or deployment.
  No full bundle retry was made to obtain a passing result.

## Evening check, 2026-10-21

Rebased onto local main `d52d7dbb`. Its four new commits change only the
tracker and task descriptions. Runtime and test sources are unchanged from
the daytime base. The static bundle consistency check passed without
regeneration. The tested branch head was `14b54a89`.

- **Branch isolation:** requested 11 separate bundle invocations of `test_rst`.
  The first four passed. Invocation five failed in 10.11 seconds at line 314
  of [the rich-preview tests]: `window.__pyStats.destroyed` was 2, not 1.
  Stopped at that failure under the steward's explicit stop rule. Did not run
  the remaining isolated checks or start the full bundle suite.
- **Fresh main comparison:** on clean main `d52d7dbb`, the same isolated
  bundle test failed on the first invocation in 8.90 seconds. It observed
  the same `2 == 1` release-count failure. This confirms that the failure
  also occurs without this change; its cause is not established.
- **Memory:** neither comparison hit a memory limit. The branch comparison
  started with 2.82 GiB available; its fifth invocation started with 2.68 GiB.
  The main comparison started with 2.76 GiB. Runs were sequential and guarded.
- **Follow-up:** [the static-suite reliability investigation][144] owns the
  release-count cause and the wide-folder wait. No RST code or assertion was
  changed here.
- **Status:** stopped as requested. Leave this issue In Progress. No merge,
  completion, acceptance, restart or deployment.

[109]: 109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions
[115]: 115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md
[130]: 130-give-served-and-browser-owned-folders-the-same-content-search.md
[ADR 0091]: ../adr/0091-server-search-stops-at-local-folder-mounts.md
[137]: 137-fix-the-intermittent-back-failure-in-test-back-retraces-the-folders-th.md
[the keyboard tests]: ../../server/tests/test_browser_keyboard.py
[139]: 139-stop-rst-previews-and-search-results-from-injecting-live-markup-securi.md
[the rich-preview tests]: ../../static/tests/test_rich.py
[ADR 0090]: ../adr/0090-revision-checked-file-replacement.md
[144]: 144-make-the-full-static-suites-pass-reliably-the-wide-folder-wait-and-tes.md
