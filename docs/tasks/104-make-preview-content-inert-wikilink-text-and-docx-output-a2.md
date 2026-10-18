# Make preview content inert: wikilink text and DOCX output (A2)

Steward issue, 2026-10-18. Goal: agentic-leverage. Step 2 of the remediation
order in `docs/ARCHITECTURE-REVIEW.md`: finding A2 (P1). Still on `main`: the
wikilink rule in `ui/adapters/preview-rich.js` turns a whole markdown-it text
token into `html_inline`, so text beside `[[note]]` renders as raw HTML
despite `html: false`, and `docxHTML` inserts converter HTML unsanitized.

## Work

Read the review's A2 section and "Remediation order" step 2 first; their
acceptance criteria are this issue's.

1. Rewrite wikilinks as link tokens, or escape all untouched text in the
   token. Malformed wikilinks are escaped.
2. Sanitize DOCX output and URL-bearing fields (DOCX, `.desktop` links)
   with an explicit safe-protocol list. Do not add a security framework.
3. Tests, red first: crafted Markdown with an event-handler image beside a
   wikilink stays inert, with and without wikilinks; links, code and
   footnotes still render; unsafe DOCX and `.desktop` URLs do not execute.
4. Document the trust boundary of bare-HTML web serving at the server root
   in `SECURITY.md`; it keeps working. Mark A2 resolved in the review, dated.

## Ground rules

- Change only what A2 needs; A8's renderer unification is separate.
- No push, deployment, restart or remote setting. Never weaken a gate.

## Acceptance

- The review's A2 acceptance holds, each point backed by a test.
- Root `uv run pytest`, both static modes and `uvx pre-commit run
  --all-files` pass; record the commands and timings here.
- Security fix: acceptance stays with Antti.
