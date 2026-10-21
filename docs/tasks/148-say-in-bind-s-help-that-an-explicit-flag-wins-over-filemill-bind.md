Steward issue, 2026-10-22 00:46 refill. Goal: agentic-leverage (Filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 20 min.

From the draft issues of [the 2026-10-22 documentation review](../reviews/2026-10-22-docs-review.md#draft-issues) ([146]): `main()` in [the CLI](../../server/src/filemill/cli.py) describes `--bind` as "overridden by FILEMILL_BIND env var", but the variable only supplies the default and an explicit `--bind` wins. The server README already describes the real behaviour.

## Work

Correct the `--bind` help text to say the variable sets the default and the flag wins. Add a focused regression test that both the precedence and the help text hold. Change no behaviour.

## Acceptance

- The help text matches execution; the new test fails on the old text and passes on the new.
- The repository's usual checks pass ([tracker rules](../../TASKS.md#rules)).
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
