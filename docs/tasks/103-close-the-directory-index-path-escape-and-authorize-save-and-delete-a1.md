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
