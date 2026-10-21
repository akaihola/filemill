Steward issue, 2026-10-22 00:46 refill. Goal: agentic-leverage (Filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 20 min.

From the draft issues of [the 2026-10-22 documentation review] ([146]): `main()` in [the CLI] describes `--bind` as "overridden by FILEMILL_BIND env var", but the variable only supplies the default and an explicit `--bind` wins. The server README already describes the real behaviour.

## Work

Correct the `--bind` help text to say the variable sets the default and the flag wins. Add a focused regression test that both the precedence and the help text hold. Change no behaviour.

## Acceptance

- The help text matches execution; the new test fails on the old text and passes on the new.
- The repository's usual checks pass ([tracker rules]).
- Memory: before each heavy command (test suite, browser, build), wait up to 10 minutes for `MemAvailable` of at least 2 GiB; if it doesn't come, start anyway at 1.5 GiB or more. Stop a running command when `MemAvailable` falls below 1 GiB or swap grows by more than 512 MiB. One heavy command at a time; bound any background job you start.
- Handoff: a short outcome and how it was verified; details go in this file. No push, publish or deploy.

## Plan

1. Add a failing CLI regression for the environment default, explicit flag
   precedence and rendered help. Cover normal and live startup.
2. Correct only the help string. Keep startup behavior unchanged.
3. Run the focused CLI and documentation checks and the full quality gate.
   Record red-green evidence and memory measurements here, then merge locally
   and complete the canonical tracker entry without accepting it.

No port or behavior changes are planned, so no ADR or architecture finding
update is needed. Browser and native suites are outside this help-only change.

## Outcome, 2026-10-22

The help now says: `Address to bind to (FILEMILL_BIND sets the default;
explicit --bind wins)`. Only the help string changed in production code.

The new regression loads a fresh CLI after setting `FILEMILL_BIND`, because
its default is read at module load. It checks the environment default, then
an explicit flag and the rendered help, in both normal and live startup.
It does not reload the shared module or start Uvicorn.

- **Red:** Both cases failed on the old help after their precedence assertions
  passed. The first green attempt exposed Rich's line wrapping in the test
  assertion. The final assertion ignores table borders and whitespace; both
  cases were checked against the old help again and failed as intended.
- **Green:** All 52 CLI, documentation and review-condition checks passed.
- **Quality:** All seven pre-commit hooks passed, including Ruff, formatting,
  mypy, Deno lint, suppression links and static bundle consistency. Deno was
  version 2.6.8. DOM-free model checks also passed. The diff review confirmed
  that runtime precedence is unchanged; `git diff --check` passed.
- **Scope:** Browser and native suites were not required for this help-only
  correction, as the contributor and testing guides allow. No architecture
  finding changed and no ADR was needed. No push, publish or deploy ran.

## Resource record

Each command ran alone under a memory guard, with a timeout and process-group
cleanup. The guard sampled memory every 0.2 seconds and would stop below
1024 MiB available or above 512 MiB swap growth. All admissions were immediate.
Negative swap growth means swap use decreased. Measurements are MiB.

| Run | Command | Outcome | Wait (s) | Admission / final available | Starting swap / growth | Elapsed (s) | Exit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Initial red | `timeout 600 uv run --project server pytest -q server/tests/test_cli.py -k test_bind_env_default_and_explicit_flag_precedence` | started at once | 0.0 | 2496.5 / 2352.5 | 2756.0 / +73.5 | 38.7 | 1 |
| Initial green attempt | `timeout 600 uv run --project server pytest -q server/tests/test_cli.py server/tests/test_docs.py server/tests/test_review_conditions.py` | started at once | 0.0 | 2366.5 / 2661.3 | 2828.1 / +3.5 | 8.42 | 1 |
| Final red | `timeout 600 uv run --project server pytest -q server/tests/test_cli.py -k test_bind_env_default_and_explicit_flag_precedence` | started at once | 0.0 | 2612.1 / 2587.1 | 2831.1 / -0.2 | 1.81 | 1 |
| Final green | `timeout 600 uv run --project server pytest -q server/tests/test_cli.py server/tests/test_docs.py server/tests/test_review_conditions.py` | started at once | 0.0 | 2575.9 / 2482.4 | 2828.4 / -2.2 | 8.58 | 0 |
| Quality gate | `timeout 1800 uvx pre-commit run --all-files` | started at once | 0.0 | 2487.0 / 2510.7 | 2826.1 / +14.5 | 18.78 | 0 |
| Model checks | `timeout 600 node ui/core/model/test.mjs` | started at once | 0.0 | 2554.6 / 2558.6 | 2839.9 / +0.0 | 0.4 | 0 |
| rebased-checks | `timeout 600 uv run --project server pytest -q server/tests/test_cli.py server/tests/test_docs.py server/tests/test_review_conditions.py` | started at once | 0.0 | 2567.2 / 2555.1 | 2844.6 / -1.0 | 2.81 | 0 |
| rebased-gate | `timeout 1800 uvx pre-commit run --all-files` | started at once | 0.0 | 2614.6 / 2495.4 | 2843.6 / +0.2 | 3.21 | 0 |

## Local integration

Rebased onto current main after concurrent work landed. A fast-forward merge
first refused because main advanced again; no files changed in that attempt.
Rebased again onto `5ce58700`, then repeated the focused checks (52 passed)
and all seven quality hooks (passed). The worktree and branch are retained.
Completion leaves the tracker unchecked, pending steward acceptance.

[the 2026-10-22 documentation review]: ../reviews/2026-10-22-docs-review.md#draft-issues
[the CLI]: ../../server/src/filemill/cli.py
[tracker rules]: ../../TASKS.md#rules
