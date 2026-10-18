# Close the directory-index path escape and authorize save and delete (A1, A3)

Steward issue, 2026-10-18. Goal: agentic-leverage (filemill is tier 1 in
`<steward-vault>/Goals.md`). This is step 1 of the remediation order in
`docs/ARCHITECTURE-REVIEW.md`: findings A1 and A3, both P1. [102]'s roadmap
audit says A1–A5 keep priority over new feature work. Both are still on
`main` (`40485493`): `app.py` serves `target / "index.html"` without
checking where it resolves, and `/api/save` and `/api/delete` check no
Origin, Host or token.

## Work

Read the review's A1 and A3 sections and "Remediation order" step 1 first;
their acceptance criteria are this issue's.

1. A1: validate the final index file against the request's zones, so an
   escaping nested `index.html` gets the same denial as its explicit URL.
   Keep in-root indexes and deliberate direct-root bookmark symlinks working.
   Audit the other derived-file responses the same way.
2. A3: add an Origin/Host check and a per-instance mutation token, validated
   before the body is read, with configured origins for reverse proxies. The
   shipped UI keeps saving and deleting through local and reverse-proxy
   origins; UI and server change together.
3. Tests, red first: a symlink matrix over resource, raw, index and mount
   routes; two-origin browser requests for save and delete.
4. Write the ADR for the mutation policy, and correct `SECURITY.md` and
   `CHANGELOG.md`, which describe the CORS removal as if it restricted
   writes. Mark A1 and A3 resolved in the review, dated.

## Ground rules

- Change only what A1 and A3 need. A2, A4 and A5 have or get their own issues.
- No push, deployment, restart of a running instance or remote setting.
- Never weaken a gate to pass it. A failure unrelated to this change gets its
  own issue with a reproduction.

## Acceptance

- An unrelated-origin POST cannot change a fixture file; a delete without
  valid authorization fails; both checks run before the body is read.
- An escaping nested index is denied at `/sub/` as at `/sub/index.html`.
- Root `uv run pytest`, both static modes and `uvx pre-commit run
  --all-files` pass; record the commands and timings here.
- Security fix: acceptance stays with Antti.


## Implementation, 2026-10-19

- Resolve the implicit index against the request's zones before FileResponse.
  Preserve direct-root bookmark symlinks. The 24-case matrix covers resource,
  raw, implicit index and mount routes with inside and outside targets.
- Authorize save and delete before path resolution or body consumption. Require
  matching Origin/Host and X-Filemill-Token, with loopback defaults and exact
  space-separated FILEMILL_ORIGINS for proxies and LAN binds. The shell supplies
  a random per-process token; the HTTP adapter sends it for both mutations.
- ADR 0081 records the policy, derived-file audit and remaining same-origin
  HTML, filesystem-race, A2, A4 and A5 limits. SECURITY.md and CHANGELOG.md now
  distinguish CORS response-read restrictions from write authorization.
- Red evidence: the initial server regression run had 23 failures and 199 passes
  in 6.03 s, including both escaping implicit indexes and unauthorized writes.
  Both two-origin browser cases overwrote the canary before the fix, failing
  in 11.09 s. After the fix both browser cases passed in 6.16 s.

Acceptance remains with Antti. No push, deployment, running-instance restart or
remote configuration change is part of this work.


## Final validation, 2026-10-19

Wall times include command startup; suites ran concurrently. No gate or
assertion was weakened.

| Command | Result | Wall time |
| --- | --- | --- |
| `uv run pytest` | 1,059 passed | 1187.33 s |
| `uv run pytest static/tests --bundle` | 147 passed | 529.77 s |
| `uv run pytest static/tests --dev` | 147 passed on full rerun | 484.59 s |
| `uvx pre-commit run --all-files` | all six hooks passed | 7.92 s |

The first development-mode run had 1 failure and 146 passes in 544.91 s wall
time. The unchanged `test_keyboard_horizontal` read scrollTop immediately after
PageDown and saw `0 -> 0`. [108] records the intermittent reproduction under
concurrent test load. A single check on unchanged main passed in 6.44 s pytest
time, then the complete development-mode rerun passed. No static source or test
was changed for [103]. Existing Docutils deprecation warnings remain.

A final manual review checked authorization before path/body access, strict
Origin/Host matching including explicit port zero, duplicate headers, stale
and missing tokens, local and configured proxy success, and final-file zone
validation. Security acceptance remains with Antti; leave the acceptance box
unchecked.
