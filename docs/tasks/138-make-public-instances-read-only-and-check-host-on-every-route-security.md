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

## Upgrade preparation

Before upgrading each reverse-proxy or LAN instance, the steward must set
`FILEMILL_ORIGINS` to every exact browser origin it serves, space-separated,
for example `https://filemill.vempai.men https://files.example:8443`.
The proxy must preserve the public Host. This setting now controls reads and
assets as well as mutations; an omitted name receives 403. Loopback names
remain allowed. No Filemill service is restarted by this task.

## Implementation plan

- Add failing public-write, token omission, UI and rebinding regressions.
- Enforce Host once before route dispatch; retain exact mutation Origin checks.
- Disable public mutation authorization and HTTP write/remove capabilities.
- Update the security policy, existing ADRs and architecture review together.
- Run the full server suite and repository gates, then merge and mark complete
  pending user acceptance.

## Validation progress (2026-10-21)

- **Red-green security checks:** the original implementation produced 41
  failures for public mutations, token exposure and foreign Hosts. The added
  malformed-IPv6 Host case also failed before the guard read the scheme
  directly from the ASGI scope. The new policy checks then passed.
- **Browser readiness:** an initial browser batch failed the fold-state
  assertion `focusCol === 1 && folded === 1`. An isolated export of main
  passed that case 20 times and passed the same 16-test sequence, so the
  failure was not established as a baseline defect. A later run found the
  Markdown-link check continuing when only the preview's Raw link existed.
  The [browser readiness checks] now wait for the expected Markdown link and
  the existing observable dial-settlement condition. Their assertions remain.
  Host validation uses direct ASGI middleware, preserving approved streams.
- **Resource limits:** one complete-suite attempt reached its 1,800-second
  timeout after 327 passing checks. A second attempt was stopped by the
  memory/swap guard after 151 passing checks. Validation therefore uses
  disjoint, sequential browser batches with the same memory limits and
  per-batch timeouts, plus the complete non-browser suite.
- **Rebase:** current main includes the preview-security repair. On the
  rebased branch, all 895 non-browser tests passed with branch coverage;
  collection contains 340 browser tests. The remaining browser batches and
  refreshed repository gates must pass before merging.
- **Deployment:** no deployed Filemill service has been restarted. The
  steward must check the origins described under Upgrade preparation first.

[browser readiness checks]: ../../server/tests/test_browser_keyboard.py
