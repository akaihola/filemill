Steward issue, 2026-10-21 22:36 refill. Goal: agentic-leverage (filemill is tier 1 on the goals page). Labelled `review` (steward decision D68). Estimated 2 h.

About 180 commits have landed on `main` since 2026-10-19: security fixes, preview and folding repairs, test isolation, the static edition and the native shell. `docs/ARCHITECTURE-REVIEW.md` was re-checked on 2026-10-20 ([132](132-re-check-the-architecture-review-against-current-main.md)) and stays out of scope, except where a living document contradicts it. Each issue updated the docs only where it touched them, so statements elsewhere may now be stale, duplicated or in conflict. Workers, reviewing agents and Antti work from these documents.

## What to do

1. Read `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, `docs/GOALS.md`, `docs/ROADMAP.md` and `docs/testing/` against the code on current `main`: commands, settings and their defaults, environment variables, file layout, test and check commands, and what each document says is done or planned.
2. Fix plain discrepancies and stale statements. Where two documents explain the same thing, keep one explanation and link to it from the other. Keep entry points short and put detail behind links.
3. ADRs in `docs/adr/` stay as written: list in the review file each ADR whose decision the code no longer follows and that doesn't say it was superseded, with the evidence.
4. Where it's unclear whether the code or the text is wrong, don't guess: list it in `docs/reviews/<run date>-docs-review.md` with the evidence and a proposed answer.
5. That file also lists each change you made, by document, with the code it now matches, and ends with a `## Draft issues` section for anything larger than a documentation fix. Don't file those issues; the steward decides.

## Constraints and acceptance

- Documentation only: no code or test changes. Leave task files under `docs/tasks/`, earlier reviews and released changelog entries as they are.
- Markdown must stay portable: `server/tests/test_docs.py` (`test_documentation_uses_portable_development_examples`) fails on private host names and home paths.
- Before merging, run the tests that read the documentation (`server/tests/test_docs.py` and any other test that opens a Markdown file; find them with `grep`). A documentation-only change doesn't need the browser suites.
- Memory: before each command, wait up to 10 minutes for `MemAvailable` of at least 2 GiB; if it doesn't come, start the command anyway when at least 1.5 GiB is available. Stop a running command when `MemAvailable` falls below 1 GiB or swap grows by more than 512 MiB. Run one heavy command (test suite, browser, build) at a time, and bound any background job you start.
- Acceptance: the review file is on `main`, every document named in step 1 was read, and each change it lists names the code it now matches.
