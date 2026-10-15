---
depends-on: []
---

# Run the static bundle, static development and server CI suites in parallel

## Evidence, 2026-10-12

[Run 38155597653](https://github.com/akaihola/filemill/actions/runs/38155597653)
on 2026-10-11 took 15m 32s. The test job ran three independent suites in
sequence: static bundle, 210.02s; static development, 214.07s; server step,
452s. Lint took 15s and browser installation took 19s.

Splitting the suites should bring feedback time to roughly eight minutes at
those durations, subject to runner availability. This is an estimate from a
failed run, not a measured target. Missing ripgrep caused four 30-second
browser timeouts in that run; its installation is already in the workflow.

## Requirements

Change `.github/workflows/publish.yml` to run the suites as three independent
jobs or matrix legs after lint:

- `uv run --project server pytest static`.
- `uv run --project server pytest static --dev`.
- From `server/`, `uv run pytest --cov=src/filemill --cov-branch --cov-report=term-missing`.

Keep all current checks, including the shared model tests and bundle freshness
check. Each browser job installs through the locked server project's
Playwright. Install ripgrep in the server job before its tests. If using a
matrix, disable fail-fast so one suite's failure does not cancel the others.
Publishing must require lint and every test suite to pass, and remain limited
to main outside pull requests.

## Acceptance

- A failing regression check first demonstrates the current serial scheduling;
  the updated workflow passes checks for independent test jobs and publication
  gating. Update existing workflow guards for the final job structure.
- CI runs all three suites concurrently after lint, and each reports its result
  even if another suite fails. A failure in any suite prevents publishing.
- Record a before/after comparison including wall time, summed runner time,
  test counts and outcomes. Faster execution must preserve the quality gate in
  `docs/ARCHITECTURE-REVIEW.md`.

## Implementation plan, 2026-10-14

1. Add structural workflow guards and demonstrate failure on serial scheduling.
2. Move shared UI and freshness checks into lint; run the three browser suites
   in a matrix after lint, with fail-fast disabled and locked browser installs.
3. Validate the quality gate, measure a GitHub Actions run against the baseline,
   and record counts, outcomes, wall time and summed runner time.
4. Rebase and merge into main, then complete the tracker pending acceptance.

## Validation, 2026-10-14

The new workflow regression first failed with
`The three suites still run serially in one job` on the original workflow
(1 failed, 3 passed). After the matrix change, the workflow and documentation
guards passed (15 passed). The guards parse YAML and verify the three exact
commands, working directories, lint dependency, disabled fail-fast, fatal
failures, unconditional suite execution, locked browser installation, server-only
ripgrep installation before tests, retained shared checks and publication gating.
PyYAML is now a locked development dependency for these structural checks.

All six pre-commit hooks and shared model checks passed. The installed Python
3.14 initially failed mypy because the conditional zstandard dependency is
absent on that interpreter. Repeating with installed Python 3.13 passed; CI
retains Python 3.12. No checks were relaxed.

GitHub rejected the branch push (`Permission to akaihola/filemill.git denied`,
HTTP 403) and workflow dispatch (`Resource not accessible by personal access
token`, HTTP 403). No updated Actions run or deployment was created. Actual
CI concurrency, timing and publication behavior remain unverified.

### Historical CI baseline

Run 38155597653 at `ea20d27dad8dd2153e6185e418b7aa2bf0de1edd`, on 2026-10-11:

| Suite | Collected | Outcome | Pytest duration |
| --- | ---: | --- | ---: |
| Static bundle | 98 | 98 passed | 210.02 s |
| Static development | 98 | 98 passed | 214.07 s |
| Server | 784 | 711 passed, 10 failed, 63 skipped | 450.50 s |

Reported workflow wall time was 932 s (15m 32s). Summed allocated runner time
was 925 s (15 s lint + 910 s test), calculated from the jobs API's start and
completion timestamps and excluding skipped publication. The server step took
452 s including invocation overhead. Publication was skipped.

### Follow-up required

With repository write and Actions dispatch permissions, push this branch and
run the updated workflow. Record job start/end timestamps and pytest totals,
confirm all three legs overlap after lint and finish independently, and verify
a failed leg blocks main publication. Compare workflow wall time and summed
runner time using the same definitions as the baseline. Preserve every check
in the architecture review. The local measurement below cannot establish a
GitHub runner speedup.

### After change: local parallel execution

The three exact workflow commands ran concurrently on the same NixOS host,
using installed Python 3.13 and the existing Nix Playwright browsers. Each
command's wall time includes uv and pytest startup. Lint ran separately and
is excluded from this local measurement.

| Suite | Collected | Outcome | Pytest duration | Process wall time |
| --- | ---: | --- | ---: | ---: |
| Static bundle | 116 | 115 passed, 1 failed | 534.62 s | 536.01 s |
| Static development | 116 | 116 passed | 559.82 s | 560.88 s |
| Server | 838 | 837 passed, 1 failed | 1162.12 s | 1163.93 s |

| Measurement | Historical CI, serial | Local after change, parallel |
| --- | ---: | ---: |
| Wall time | 932 s | 1163.95 s |
| Summed runner/process time | 925 s | 2260.82 s |
| Collected test invocations | 980 | 1070 |
| Passed / failed / skipped | 907 / 10 / 63 | 1068 / 2 / 0 |
| Overall outcome | Failure; publication skipped | Failure; no publication attempted |

These are different hosts and revisions, with different test counts. This
comparison records observations, not a CI speedup. The matrix uses three
separate GitHub runners; this local run shared one host. The increased counts
include intervening main changes and this task's one new server workflow test.
Server coverage was 90% combined statement/branch coverage. No tests, coverage
flags, skips or failure rules were changed to improve timing.

The bundle failure was
`static/test-ui.py::test_touch_tap_opens_folder_first_time`: the row menu stayed
hidden after a long press, timing out after 3 seconds. An isolated rerun passed
(1 passed in 4.99 s); the complete suite result remains failed.
The server failure was
`tests/test_browser_new_ui.py::test_a_git_bundle_opens_as_refs_then_files_and_a_file_previews`:
opening repo.bundle did not populate the next column before a 15-second timeout.
An isolated rerun also failed (1 failed in 18.58 s). The same test was then
run from unchanged main using the worktree's Python environment to check
whether the failure predates the workflow change. That run passed (1 passed
in 3.81 s), so the cause of the worktree-only timeout remains unresolved; it
cannot be claimed as a reproduced main failure.
The frontend and server implementation were unchanged by this task.

The worktree issue remains In Progress. Merge, tracker completion and deployment
are deferred pending a passing quality gate and the required actual CI
measurement; user acceptance has not been checked.

### Rebase integration

Main advanced during validation with [91]'s `--durations=20` reporting and
[92]'s concurrency scope. The rebase preserves both. Workflow guards from those
changes now check named matrix legs and disabled fail-fast rather than serial
step names and `!cancelled()` conditions. Publication guards require both lint
and the full matrix. The local full-suite measurement above preceded this
rebase and did not include duration reporting. Final structural checks cover
the integrated workflow; a new complete CI measurement remains required.

Final integrated validation: 19 workflow/documentation tests passed, all six
pre-commit hooks passed, and no conflict markers remain in the changed files.

## Measured GitHub Actions comparison, 2026-10-15

[Parallel run 38767593452](https://github.com/akaihola/filemill/actions/runs/38767593452)
tested `ca1446b7172a9cd6d7af17f943b2eafe2fc89bad`. Lint finished at
16:16:46 UTC. All three matrix jobs started at 16:16:49 UTC on separate
runners. The bundle job failed at 16:20:48; development continued until
16:21:13 and server until 16:28:31. This directly verifies independent
execution after a failed leg. Publication was skipped; YAML regression guards
also verify lint/matrix dependencies, fatal failures and main-only publication.

The closest successful serial baseline is
[run 38564017994](https://github.com/akaihola/filemill/actions/runs/38564017994),
on 2026-10-14 at `9c67d665098875b01da5b7b14be7dc897ad65dd4`.

| Suite | Serial baseline | Parallel run |
| --- | --- | --- |
| Static bundle | 116 passed, 239.95 s | 115 passed, 1 failed, 209.65 s |
| Static development | 116 passed, 241.81 s | 116 passed, 223.51 s |
| Server | 841 passed, 676.34 s | 842 passed, 666.05 s |
| Collected invocations | 1073 | 1074 |
| Workflow wall time | 1239 s (20m 39s) | 725 s (12m 05s) |
| Summed lint/test runner time | 1211 s | 1221 s |
| Publication runner time | 15 s, successful | 0 s, skipped |
| Overall outcome | Success | Failure |

Workflow wall time uses the run's created_at and updated_at timestamps.
Summed runner time adds non-skipped job start/end durations, including setup
and cleanup; publication is shown separately. The parallel jobs used 239 s,
264 s and 702 s; lint used 16 s. Pytest durations in the suite rows exclude
job setup. Wall time fell by 514 s (41.5%); lint/test runner time increased
by 10 s (0.8%). This is one observation across runs with different outcomes,
not a guaranteed speedup. The extra server test is this task's matrix guard.
All tests were collected, and server statement/branch coverage remained 90%.
The original failed 2026-10-11 baseline remains recorded above.

The failing bundle test was `static/test-rich.py::test_markdown_viewport`,
which counted 0 table cells instead of 20 after a preview rebuild. Main had
already fixed this asynchronous test race in `efa92fd` while the feature branch
was waiting for push/dispatch permission. The branch is now rebased onto main,
including that fix and main's shared browser fixtures. The repaired test passed
locally (1 passed in 5.69 s); all 19 workflow/documentation tests and all six
pre-commit hooks passed after rebase. No new test repair was added by [90].

The historical notes about denied push/dispatch remain above to explain the
delay. The user pushed and dispatched the measured run from atom. A passing
confirmation run of the rebased branch is still required before merge and
completion. The issue remains In Progress, pending that validation.
