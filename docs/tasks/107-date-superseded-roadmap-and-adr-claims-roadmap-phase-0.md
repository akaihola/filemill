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
