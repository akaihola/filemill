---
depends-on: [99]
---

# Check the 19 newest review-queue items against the acceptance policy

Steward issue, 2026-10-17 (decisions D7 and D10 in
`<steward-vault>/agents/steward/decisions.md`). It takes over vault
[18], whose tracker is blocked. The verdicts feed the steward's next digest,
so that Antti can accept or reject these items with less checking of his own.
Antti's first calibration lesson: run the tests a packet names before offering
an item.

## Items

The `- [ ]` items under `## Completed / Accepted` whose Hai `updatedAt` is from
2026-10-17, except [96], a history rewrite left to Antti, and this issue's
prerequisite [99]. Most moved there through [95]'s reconciliation; read [95]'s
notes in `docs/tasks/95-*.md` for them. [95] itself, [97], [98], [30] and the
`wait_for_timeout` `[*]` are among them.

## Work

Run after [99], so that `main` carries [25]'s pytest migration and, ideally,
green suites. Read each item's description and the commits that delivered it.
Run the tests the description names on current `main`, in bundle and dev mode
where static tests apply. If a suite fails on `main`, name the failure, whether
an item caused it, and whether an issue covers it; don't count it against an
item that didn't cause it. Check criterion 3 with `git revert --no-commit` of
an item's commits in a temporary worktree (`git worktree add --detach
"$TMPDIR/revert-check" main`, removed afterwards); conflicts only in `TASKS.md`
and `docs/tasks/` don't count.

For each item, record one line: issue, a one-line outcome, the evidence
(commits, files, test command with pass and fail counts) and a verdict under
`<steward-vault>/agents/steward/acceptance-policy.md`:

- **would accept:** all four criteria hold; give the revert command;
- **left to Antti:** name the criterion or the "Always left to Antti" class;
- **not done:** say what is missing.

## Deliverable

A section `## Evidence, YYYY-MM-DD` in this description file, with the lines
grouped by verdict and the counts per verdict at the end.

## Ground rules

- Change no other issue's state or text, and never change `[ ]` to `[x]`: only
  Antti accepts.
- Don't push, and don't touch the vault.

## Acceptance

- Every listed item has a line with evidence and a verdict.
- Nothing outside this file and the issue's own tracker moves changed.
