Steward issue, 2026-10-22 06:17 refill (steward decisions D53 and D95: whole-repository architecture review aimed at simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Label `review`. Estimated 1.5 h.

filemill is the most active repository (239 commits on `main` since 2026-10-19) and has never had a whole-repository architecture review. Its [2026-10-22 docs review](../reviews/2026-10-22-docs-review.md) and [2026-10-21 security review](../reviews/2026-10-21-security-review.md) already cover docs and security.

## Work

1. Read `README.md`, `AGENTS.md`, `CONTRIBUTING.md` and `docs/`, then `server/`, `ui/`, `static/` and `native/`, and the tests.
2. Apply the `honey` principles (speculative generality, hand-rolled stdlib, single-caller abstractions, dead code, narration) and the `codebase-design` deep-module vocabulary, using those skills if your session has them: where a seam would make a module smaller to change and easier to test, where two code paths do the same job (for example served and browser-owned folders), and what can be deleted.
3. Write `docs/reviews/2026-10-22-architecture-review.md`: findings ranked by benefit per hour, each with file and line evidence on `main`, what changes if it is fixed, and a drafted issue (title, work, acceptance, about an agent hour each). Mark drafts that overlap open issues in `TASKS.md` (including In Progress [130] and [141]) or findings of the two reviews above instead of duplicating them.

## Ground rules

- Architecture only. Don't probe for vulnerabilities or write exploit reproductions.
- Read-only apart from the report and this issue's tracker moves. Don't file the drafts; the steward files them.
- Run no browser suite; at most one focused test command at a time, under your launch prompt's memory rule.
- Keep private paths and host names out of the report (the docs tests reject them).

## Acceptance

- Every finding cites code on `main` and says what changes if it is fixed.
- The report ends with a `## Draft issues` section and names the three drafts to do first, and why.
- The repository's documentation tests still pass with the new report.
- Handoff: a short outcome; details go in the report and this task record.

Tracker: [the filemill tracker](../../TASKS.md).

## Review record, 2026-10-22

- **Start:** the canonical main tracker moved to In Progress in commit
  `c6fcd0e9`. The move left no staged or unstaged tracker changes. The worktree
  rebased onto that commit before the review.
- **Snapshot:** main `c6fcd0e97964f7855d2902d53c23cce87f6e7943`.
  The opening brief's claim of no architecture review is historical:
  [docs/ARCHITECTURE-REVIEW.md] already exists. Shared content search was
  Completed / Accepted, unchecked, at this snapshot; fixture isolation remained
  In Progress. These corrections do not change the original requirements above.
- **Work:** read guidance and prior reviews, traced server/shared-UI/static/native
  boundaries and relevant tests, checked callers, ranked bounded changes and
  wrote [docs/reviews/2026-10-22-architecture-review.md]. Applied `honey`;
  `codebase-design` was unavailable. No delegation or external messaging.
- **Outcome:** six findings and six unfiled drafts, each tied to main source
  lines and acceptance criteria. Five refine existing A7/A8/A9/A12 findings;
  the common boot initializer is the independent proposal. Recommended first:
  remove the unreachable Python VTT renderer, hoist SQLite row-key facts and
  centralize UI boot wiring. Preserve VTT's small registered listing contract:
  deleting it would also change API and URL behavior.
- **Scope:** only the report and this task record change on the feature branch.
  Tracker moves use the canonical checkout. Application code and tests remain
  unchanged; no port or behavior decision needs a new ADR in this review.
  Browser/native suites, full runtime suites, live-instance probes, benchmarks
  and deployment are outside this documentation-only change. Proposed fixes
  require their own regressions; this review does not establish runtime fixes.

## Verification

The focused documentation command passed before the report (**33 tests,
1.03 s**), after it (**33 tests, 4.77 s**) and with the task record included
(**33 tests, 3.26 s**):

```bash
timeout 600 uv run --project server pytest -q server/tests/test_docs.py server/tests/test_review_conditions.py
```

The full quality gate passed all seven hooks: Ruff, Ruff format, mypy,
Deno format, Deno lint, Python suppression links and bundle consistency.

```bash
timeout 600 uvx pre-commit run --all-files
```

A lightweight check verified the report's 45 local reference destinations,
headings of at most 60 characters, six findings, six drafts and the final
`## Draft issues` section. `git diff --check` passed. No browser was launched.

## Memory admission and command outcomes

Each guarded command ran alone. The guard admitted at 2,048 MiB available,
allowed a fallback only after ten minutes at 1,536 MiB, and monitored available
memory and swap every 0.25 seconds. It would terminate the process group below
1,024 MiB available, above 512 MiB additional swap, or at its 1,200-second outer
deadline. Focused checks also had their own 600-second timeouts. Values below
are MiB; elapsed time includes command setup, not just pytest's test time.

- **Source/document inventory — started at once.** `rg --files` over the
  four source/document trees, excluding generated index and binary assets.
  Wait 0.00 s; admission 2,756.6; final 2,747.9; starting swap 2,453.8;
  swap growth 0.0; elapsed 0.25 s; exit 0.
- **Baseline documentation checks — started at once.** The focused pytest
  command above. Wait 0.00 s; admission 2,737.6; final 2,776.2;
  starting swap 2,451.6; swap growth -0.2; elapsed 5.75 s; exit 0.
- **Whole-repository caller search — started at once.** `rg -n` for
  `VTTProvider`, `vtt_provider`, `previewFormat`, `render_source`, `is_vfs_file`,
  `_HTML_EXTS` and `FILEMILL_LIVE`, excluding the generated index and minified
  assets. Wait 0.00 s; admission 2,575.3; final 2,578.1;
  starting swap 2,453.6; swap growth 0.0; elapsed 0.25 s; exit 0.
- **Report documentation checks — started at once.** The focused pytest
  command above. Wait 0.00 s; admission 2,775.2; final 2,703.9;
  starting swap 2,542.4; swap growth -0.8; elapsed 23.93 s; exit 0.
- **Full quality gate — started at once.** The pre-commit command above.
  Wait 0.00 s; admission 2,740.3; final 2,699.2; starting swap 2,541.1;
  swap growth -1.0; elapsed 37.51 s; exit 0.
- **Final documentation checks — started at once.** The focused pytest
  command above, including the task record. Wait 0.00 s;
  admission 2,830.9; final 2,812.0; starting swap 2,535.2;
  swap growth 0.0; elapsed 17.98 s; exit 0.

## Integration

Report commit `92d4d0eb` was rebased on main (no intervening changes) and
fast-forwarded into the canonical main checkout after validation. The report
keeps its original evidence commit. The worktree and branch are retained.
No runtime deployment is needed for these two documentation files. Completion
uses the separate tracker-only move, with acceptance left unchecked.

[docs/ARCHITECTURE-REVIEW.md]: ../ARCHITECTURE-REVIEW.md
[docs/reviews/2026-10-22-architecture-review.md]: ../reviews/2026-10-22-architecture-review.md
