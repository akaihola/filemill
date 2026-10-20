---
depends-on: [137]
---

Steward issue, 2026-10-21 02:45. Goal: agentic-leverage (filemill is a tier 1 project in `<steward-vault>/Goals.md`). Estimated 2 h.

[The 2026-10-21 security review](../reviews/2026-10-21-security-review.md) ([136]) found two request-authorization gaps; this issue fixes both, because both change how `app.py` and `mutations.py` decide who may do what:

- **S1, "A public instance accepts saves and deletes":** `--public` only hides dotted paths. Save and delete stay on, every public shell carries the mutation token, and `mutations.authorized` trusts the Origin and Host text. Whether a visitor can write today depends on the proxy in front, not on Filemill.
- **S3, "Read routes accept any Host, so DNS rebinding reads the root":** only save and delete check Host. `api_dir`, `api_search`, `api_raw`, `api_preview` and `resource` answer any Host, so a page whose name rebinds to loopback reads a private root, dotfiles included. ADR 0081 claims the allowlist covers this.

It depends on [137], because a red suite blocks every merge.

## What to do

1. Read S1 and S3 with their evidence in the review.
2. S1: make a public instance read-only. It serves no mutation token, its UI offers no save or delete, and `api_save` and `api_delete` refuse with 403 whatever the headers say. Test it in `server/tests/test_public_mode.py`, replacing the assertion that a public shell carries the token.
3. S3: apply the Host allowlist to every route, reads included, in one place (a middleware or one shared check), with the same allowed names as the mutation check. Test a rebinding-style request (loopback peer, foreign Host) against each read route.
4. Deployed instances sit behind reverse proxies and answer under names other than loopback. Keep one documented setting that lists the extra allowed host names (reuse `FILEMILL_ORIGINS` if it fits), and write in the issue file and in the changelog which setting an operator must set before upgrading, so the steward can check each deployed instance first.
5. Correct SECURITY.md's public-instance section and ADR 0081's Host claim to match.

## Constraints and acceptance

- Memory: before each command, wait up to 10 minutes for `MemAvailable` of at least 2 GiB; if it doesn't come, start the command anyway when at least 1.5 GiB is available. Stop a running command when `MemAvailable` falls below 1 GiB or swap grows by more than 512 MiB. Run one heavy command at a time, and bound any background job you start.
- Don't restart any Filemill service; the steward does that after checking each deployed instance's host names.
- Acceptance: the new tests pass; a public instance refuses save and delete and carries no token; every read route refuses a foreign Host; local use on loopback works unchanged; the full server suite is green, and the docs match the code.
