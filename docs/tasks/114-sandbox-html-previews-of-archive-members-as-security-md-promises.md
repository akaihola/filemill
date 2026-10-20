Steward issue, 2026-10-19 21:00. Goal: agentic-leverage; filemill is tier 1.
From question 1 of [[109]](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md)'s
docs check. Labelled `security`.

`SECURITY.md` promises that HTML previews are sandboxed. A file on disk gets an
`<iframe sandbox="">` (`ui/core/renderers.js`), but an `.html` member of an
archive is previewed through `/api/preview?v=` by `_preview_html` in
`server/src/filemill/preview.py`, whose `<iframe>` has no `sandbox` attribute.
Checked on `main` at 21:00 on 2026-10-19: still none. So a crafted archive can
run script in the preview with filemill's origin.

## What to do

1. Write a failing test that previews an archive's `.html` member and asserts
   the iframe is sandboxed (no `allow-scripts`, no `allow-same-origin`), in both
   editions if both render it.
2. Give the server-rendered iframe the same sandbox as the file-on-disk path,
   and check whether any other server-built preview iframe lacks it.
3. Note the fix in `SECURITY.md` only if its wording needs to change.

## Constraints and acceptance

- Security fix: Antti accepts it, not the steward.
- No push, no deploy, no service restart.
- Memory: before each browser or test command, wait up to 10 minutes for
  `MemAvailable` of at least 2 GiB; if it doesn't come, start anyway when at
  least 1.5 GiB is available. Stop a running check, and record it as
  unavailable, when `MemAvailable` falls below 1 GiB or swap grows by more than
  512 MiB.
- The new test fails before the fix and passes after; the server suite passes.

## Implementation, 2026-10-20

- Only the server edition renders archive members. The static edition and
  the browser's local-folder mount have no archive provider, so both new tests
  are server tests:
  `test_an_html_member_previews_in_a_sandboxed_iframe` in
  [test_api.py](../../server/tests/test_api.py) and
  `test_an_html_member_previews_in_a_sandbox` in
  [test_browser_new_ui.py](../../server/tests/test_browser_new_ui.py). The
  browser test's member page writes to the app page through `parent`. Before
  the fix the write landed (`dataset.pwned == 'yes'`), so the member's script
  ran with Filemill's origin.
- `_preview_html` in [preview.py](../../server/src/filemill/preview.py) now
  gives its iframe `sandbox=""`, the sandbox
  [renderers.js](../../ui/core/renderers.js) gives an HTML file on disk.
- The only other server-built preview iframe is `_preview_pdf`'s. It stays as
  it is, like the browser's PDF iframe for a file on disk. The raw route
  serves a `.pdf` member as `application/pdf`: a member named `evil.pdf`
  holding `<script>` came back with that type, so it is not parsed as a page.
- [SECURITY.md](../../SECURITY.md) now names archive members in the preview
  boundary. It also says that a member's Raw link opens it from `/api/raw` as
  a same-origin page, as the server serves an HTML file at the root. A
  `Content-Security-Policy: sandbox` header on that response would close it;
  that is a separate decision, not part of this issue.

## Validation, 2026-10-20

Each test command waited for `MemAvailable` of at least 2 GiB; none had to
wait or stop. Swap grew by at most 54 MiB.

- Before the fix: both new tests failed. The API test found
  `<iframe src="/api/raw?p=site.zip&amp;v=page.html">`, and the browser test
  read `'yes'` from the app page.
- After the fix: both pass, with the rest of
  [test_preview.py](../../server/tests/test_preview.py) and every test whose
  name mentions `html` (58 passed).
- Server suite: 973 passed, 1 failed in 9 min 55 s. The failure was
  `test_documentation_uses_portable_development_examples`, which could not
  read the sandbox-masked `.claude/loop.md`. Re-run outside the sandbox,
  `test_docs.py` and `test_suppression_links.py` passed (31 tests).
- `ruff check server`, `ruff format --check server/src server/tests` and
  `mypy server/src` are clean. No file under `ui/` changed, so the Deno and
  `build-index.py --check` gates do not apply.
