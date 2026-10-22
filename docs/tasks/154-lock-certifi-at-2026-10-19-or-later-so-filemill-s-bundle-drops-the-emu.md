Steward issue, 2026-10-22 08:54 refill (steward decision D98: confirmed exposure gets focused fixes). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Estimated 20 min.

This is draft 5 of the vault's 2026-10-22 eMudhra and PHP exposure check (`<steward-vault>/../docs/reviews/2026-10-22-emudhra-and-php-exposure.md`). Filemill's server makes no outbound HTTPS, so this is hygiene: the locked `certifi` (2026.2.25) still carries the compromised roots.

## Work

Bump `certifi` in `uv.lock` to 2026.10.19 or later with `uv lock --upgrade-package certifi`; change nothing else in the lock.

## Acceptance

- `uv run python -c 'import certifi; print(certifi.__version__)'` prints 2026.10.19 or later.
- The lock diff touches `certifi` only, and the server's focused test command passes.
- No service restart is needed for this change; don't restart `filemill` or `filemill-public`.

## Ground rules

- Keep private paths and host names out of committed docs and code (the docs tests reject them). The check receipt (`*.evidence.json`) is exempt.
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker].

[the filemill tracker]: ../../TASKS.md


## Implementation, 2026-10-22

Updated [the workspace lock] with `uv lock --upgrade-package certifi`.
The selected version is 2026.10.19. Only certifi's version and distribution
metadata changed. No application code, port or architecture finding changed;
no ADR is needed. Neither service was restarted.

The version-floor assertion failed first on 2026.2.25, then passed on
2026.10.19. The focused server command passed 144 tests:

```bash
timeout 600 uv run --project server pytest -q server/tests/test_api.py server/tests/test_app.py server/tests/test_cli.py server/tests/test_docs.py server/tests/test_review_conditions.py
```

`timeout 600 uvx pre-commit run --all-files` passed all seven hooks.
Clean merged-commit acceptance checks are recorded in [the check receipt].
Browser and native suites are outside this dependency-only change.

## Resource checks

Each guarded command had a 600-second timeout. Memory values are MiB.
Both commands started at once, with a 0-second admission wait and exit code 0.

| Command | Admission | Final | Starting swap | Swap growth | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Focused server command above | 3158 | 3065 | 2182 | -4 | 21.1 |
| Pre-commit gate above | 3154 | 3036 | 2178 | 0 | 14.5 |

[the workspace lock]: ../../uv.lock
[the check receipt]: 154-lock-certifi-at-2026-10-19-or-later-so-filemill-s-bundle-drops-the-emu.evidence.json


## Merged verification

Delivery commit: `105654ae81424a7a7caf3ed77fb3ba19d569693c`.
The clean checkout at that commit passed all four recorded checks:
version floor, certifi-only lock diff, 144 focused server tests, and the
seven-hook quality gate. Exact commands, dependency fingerprints and results
are in the check receipt. All acceptance checks passed; no follow-up is needed.

The evidence recorder used a 650-second outer timeout for each check.
All four record commands started at once, waited 0 seconds and exited 0.
The recorder's exact commands are in the receipt's `resource_checks`.

| Recorded check | Admission | Final | Starting swap | Swap growth | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| version | 3037 | 3013 | 2163 | -2 | 2.0 |
| lock-scope | 3049 | 3038 | 2155 | 0 | 1.0 |
| focused-server | 3038 | 3051 | 2155 | 0 | 13.6 |
| quality-gate | 3058 | 3043 | 2155 | 0 | 3.0 |
