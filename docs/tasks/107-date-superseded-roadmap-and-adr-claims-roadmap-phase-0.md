---
depends-on: [105]
---

# Date superseded roadmap and ADR claims (roadmap Phase 0)

Steward issue, 2026-10-18, filed from [102]'s audit. Goal: agentic-leverage.

The work, ground rules and acceptance are **Draft 0B** in
`docs/tasks/102-audit-the-technical-roadmap-against-main-and-draft-the-next-phase-s-is.md`,
section "Next issue drafts", including its proposed roadmap status patch.
Follow them as written, including "All drafts inherit these ground rules".

Antti has not answered the draft's policy question (replace the under-40-line
ADR rule, the 1,500-line and four-dependency server budgets and the
one-task-per-phase claim with evidence-based criteria). So keep those
policies and annotate their failed checks explicitly, as the draft says for
that case; do the factual supersession notes in full. Record validation and
remaining limits here.

## Implementation plan, 2026-10-19

1. Apply dated status notes for all ten roadmap phases using [102]'s audited
   baseline and later main changes [103]–[106]/[108]. Retain the one-task,
   under-40-line ADR and server budget policies, with explicit failed checks.
2. Date supersession of ADR 0001's upload renderer, ADR 0005's lastSel and
   ADR 0034's read-only contract. Preserve their original text and measurements.
3. Record historical test/editor corrections here. Both the named task 2 file
   and completed editor-cursor item were retired by `c7b7f38b`; inspect their
   pre-deletion versions without restoring retired tracker entries. Preserve
   the original failures, acceptance and later outcomes through Git references.
4. Date A11's corrected facts and remaining work. Clarify only the existing
   Linux native prototype in GOALS; cross-platform applications stay a goal.
5. Run documentation checks, pre-commit and diff/link checks. Rebase and merge
   locally, then complete only [107], unchecked pending user acceptance.

This is prose-only work. No new guard or behavior is planned, so no new test
is needed. Existing documentation checks validate the correction. No push,
deployment, restart or remote settings change is authorized by Draft 0B.

## Historical record corrections, 2026-10-19

The two named records are absent from today's tree. Retirement commit
`c7b7f38b` removed `docs/tasks/2-fix-all-test-failures.md` and the completed
"Text file editing should start with the cursor at the top of the file" item.
Their original text remains in `c7b7f38b^`. No deleted record is restored and
no other issue's text, state or user acceptance is changed here.

### Retired task 2

Read with `git show c7b7f38b^:docs/tasks/2-fix-all-test-failures.md`.
Its original failure inventory remains historical evidence: main `de104f5`
on 2026-09-01 had 21 failed and 843 passed in 13:20. It fixed a
`layout=no-columns` test assumption and missing `data-hidden` propagation,
then delegated 19 legacy HTMX keyboard failures to the shared-UI migration.
Its original completion claim was a green server suite with no disabled or
deselected tests. Reverification on `85ffe6d`, 2026-09-02, recorded 870 passed
in 270 s and 31 keyboard tests passed in 130 s, with browser setup enabled.

Those are measurements of the named historical commits, not instructions for
today. Its claims that `/f/` still serves HTMX and ten tests still drive it
were overtaken by HTMX deletion, recorded in [102] Phase 0.1 at `a6535049`,
`0fd40da9` and `686cd25d`. ADR 0067 later removed `layout=no-columns` on
2026-09-25. Do not restore either route/layout to satisfy the old test.
The `-p no:randomly` advice and blanket prohibition on concurrent Playwright
runs describe the old harness. Current test commands are in CONTRIBUTING.md;
[90] now runs separate suites in parallel CI jobs. This does not prove root
`pytest -n auto` works. Task 2's counts establish neither current coverage nor
current main CI delivery.

### Retired editor-cursor item

Read with `git show c7b7f38b^:TASKS.md`; the completed item requested editing
at the top of the file. Its original acceptance remains. Later [12] reported
both "edit starts at the top" checks failing alongside a `.pv-content`
timeout. That later report is distinct from the earlier completed claim;
do not erase either or treat retirement as proof against a regression.

Current `ui/editor/editor.js` focuses the textarea, calls
`setSelectionRange(0, 0)` and sets `scrollTop = 0`.
`static/tests/test_ui.py::test_edit_mode` checks zero selection endpoints and
scroll position for both long plain text and highlighted source. [25]/[99]
replaced the old monolithic static scripts with pytest sections; [99]/[101]
record later passing bundle/dev suites including these editor checks. These
later outcomes address the reported failures, without changing the original
acceptance or claiming a new browser-suite run for this prose-only issue.

## Validation and remaining limits, 2026-10-19

- `uv run pytest server/tests/test_docs.py -q`: 20 passed, repeated after
  historical corrections with 20 passed in 1.02 s.
- `uvx pre-commit run --all-files`: all seven hooks passed, including the
  suppression-link guard added by [106]. The draft's six-hook count predates it.
- `git diff --check`: passed. Only Markdown files change.
- Mechanical review confirmed ten dated phase statuses and every original
  roadmap line retained in order. Removing the three added ADR notes reproduces
  their original files byte for byte. All newly added Markdown link targets
  resolve. A first broad link scan encountered the existing TASKS.md example
  `~/note.md`; the new-link-only check excludes unchanged examples.
- Budget checks against main `25bc4d4e`: 2,597 production Python lines,
  sixteen ADRs at least 40 lines before this patch, six declared runtime
  dependencies, and two function-local compatibility imports at
  `providers/archive.py:60` and `:68`. The retained policies explicitly fail.
  No code or measurement was cut to make a policy pass.
- Task 2 and the editor-cursor item were inspected in `c7b7f38b^`; retirement
  in `c7b7f38b` explains why corrections are recorded here. Original evidence
  and acceptance remain in Git. [12]'s later failures and [99]/[101]'s passing
  outcomes are distinguished from the earlier completed item.

No new guard or implementation bug fix was introduced. Existing documentation
checks provide validation; full browser suites were not rerun. [93]/[94] remain
In Progress and still require delivered-main CI proof. No user acceptance was
changed. No push, deployment, service restart or remote setting change occurred.
A4/A5 and A6–A10 remain open, along with Phase 2 consolidation, a clean command
audit, native release parity and the unanswered policy decision. This patch
only dates factual claims; it does not waive policy or resolve those limits.
