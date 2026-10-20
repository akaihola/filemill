Steward issue, 2026-10-20 22:30. Goal: agentic-leverage (filemill is tier 1). Labelled `security` (security reviews stay on Claude, steward decision D68). Estimated 1.5 h.

Filemill serves files over HTTP, including a public instance, saves and deletes files, opens archives and Git bundles, and renders untrusted content in previews. Its architecture review (re-checked 2026-10-20 by filemill [132]) fixed three security findings, A1 to A3, but the repository has never had a whole-tree security review. A whole-repository scan is on [the steward's improvement menu](http://hopeli/my-knowledge/agents/steward/spare-quota.md?f).

## Work

1. Use the `security-review` skill over the tree, weighting what an outside visitor can reach: `server/src/filemill/` (`app.py`, `api.py`, `mutations.py`, `paths.py`, `urls.py`, `vfs.py`, `preview.py`, `pwa.py`, `providers/`), then the UI's adapters and service worker, the native host, and `tests/` fixtures.
2. Look for: path traversal or symlink escape out of a served root, including through archives, bundles and virtual paths; requests that reach save, delete or other mutations without the authorization `SECURITY.md` describes; content that can run script as Filemill (previews, Raw views, SVG, HTML inside archives, Markdown); denial of service from unbounded reads, archive bombs or slow Git commands; cache or service-worker behaviour that serves one visitor's data to another or keeps it after logout; anything the public instance exposes that a private one shouldn't; and secrets committed in the tree or history (`git log -p` searches: name the file and commit, never the value).
3. Check `SECURITY.md`'s threat model against what the code does, and list each claim that doesn't hold.
4. Write the report to `docs/reviews/2026-10-21-security-review.md`: findings ranked by impact and likelihood, each with file and line evidence, and a drafted issue (title, work, acceptance) for each fix worth making. Don't duplicate open issues or the review's A4 to A14; refer to them instead. Link paths as relative links. Don't fix anything in this issue.
5. A live credential in the tree or history is urgent: say so first in your completion message, with its location only.

## Acceptance

- The report exists, covers every area in step 1 or says why it was skipped, and drafts an issue for each finding worth fixing.
- No secret value appears in the report, the commit or the thread.
- Read-only: no code or config change, deploy, push, service restart or probing of a live instance; read the code instead.
- The documentation test (`server/tests/test_docs.py`) still passes for the new report. Memory: wait up to 10 minutes for 2 GiB `MemAvailable`, start at 1.5 GiB or more, stop below 1 GiB or on 512 MiB of swap growth.
