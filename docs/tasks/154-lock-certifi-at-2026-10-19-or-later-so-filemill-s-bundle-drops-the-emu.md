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

Tracker: [the filemill tracker](../../TASKS.md).
