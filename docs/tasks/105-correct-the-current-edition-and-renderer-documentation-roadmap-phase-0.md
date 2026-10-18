---
depends-on: [102]
---

# Correct the current edition and renderer documentation (roadmap Phase 0)

Steward issue, 2026-10-18, filed from [102]'s audit. Goal: agentic-leverage.

The work, ground rules and acceptance are **Draft 0A** in
`docs/tasks/102-audit-the-technical-roadmap-against-main-and-draft-the-next-phase-s-is.md`,
section "Next issue drafts". Follow them as written, including "All drafts
inherit these ground rules". Read `docs/ARCHITECTURE-REVIEW.md` first.

Where the security issues filed beside this one (A1/A3, A2) have landed,
describe their behaviour as current; otherwise do not claim A1–A5 fixed.
Record validation and remaining limits here.

## Implementation and validation, 2026-10-19

Scope followed Draft 0A: verify the four current guides against renderer,
startup and CI code; consolidate shared facts in the root README; date the A11
corrections; retain the old local-folder measurements as historical evidence.
No application behavior, product policy or security authority policy changed.

- Root README now has the edition/renderer matrix and implementation links.
  PPTX is local slide-text extraction, not a full Office viewer. DOCX is HTML
  conversion, not exact page layout. Static rich imports follow the remembered
  switch; server Markdown/DOCX use vendored modules; served RST uses Python.
- Server guidance removes the retired renderer/upload pipeline from current
  instructions and distinguishes CLI root/live options from ASGI environment
  lookup. Source and packaging descriptions match current module graphs.
- Static guidance describes FSA writes/deletes and permissions, CDN downloads
  and document resource requests. Existing scoped test instructions remain.
- A11 corrections are dated. A1/A3 are current via [103]; A2, A4 and A5 remain
  open. No security fix is attributed to this documentation change.

Validation:

- Red: `uv run pytest server/tests/test_docs.py -q` reported 8 failed,
  12 passed before the prose corrections. The new cases cover retired claims
  and the CLI option/environment table.
- Green: the same command passed all 20 tests.
- `uv tool run pre-commit run --all-files`: all six hooks passed, including
  ruff, ruff-format, mypy, deno-fmt, deno-lint and build-index.
- `uv run pytest server/tests/test_cli.py -q`: 9 passed. These tests mock
  Uvicorn and verify root, bind and reload arguments without starting services.
- Local Markdown prose link targets checked against the checkout. Links inside
  fixture-creation commands were excluded, since those commands create targets.
- Startup examples checked against `cli.py:main`, `app.py` ROOT initialization
  and `env.py:env`. Static serving/build commands match `static/build-index.py`
  and the existing development entry point. No service was started or restarted.

Remaining limits:

- Browser-owned RST still incorrectly routes to the server, architecture A8.
- PPTX has no layout, images or animation rendering. Choosing a new viewer is
  outside this factual correction. Existing later PPTX work retains its scope.
- A2 preview trust, A4 save integrity and A5 caching/offline recovery are open.
  The rich-preview switch does not block every document network request.
- Superseded roadmap/ADR policies remain [107] work. Historical measurements
  were preserved. Full browser suites were not rerun for this prose-only change.
- Draft ground rules prohibit push, deployment and restart; none was performed.
