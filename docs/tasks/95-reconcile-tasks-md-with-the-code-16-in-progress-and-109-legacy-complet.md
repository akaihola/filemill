---
depends-on: [96]
---

# Reconcile TASKS.md with the code: In Progress and legacy completions

`## In Progress` holds 16 issues that no pacer thread is working on, and
`## Completed / Accepted` holds 109 `[ ]` issues without Hai timestamps. Most of the
latter came from the 2026-09-29 migration "docs(tasks): unify completion and
acceptance", which moved the old `## Completed` section in as "awaiting
acceptance". At least one ("Virtualise column rows") seems never to have been
implemented. Antti cannot review 109 items one by one.

For each issue in those two groups, check the code and history (`git log -S`, the
named files, tests, ADRs):

- In Progress, implemented: move to `## Completed / Accepted` as `[ ]` (tracker
  rules). In Progress, not started: move to `## Ordered backlog`.
- Legacy completed, implemented: leave as is.
- Legacy completed, not implemented or only partly: leave the state alone and list
  it.

Write the findings to this issue's description file: one table row per issue with
its reference, verdict, and evidence (commit hash or file), and at the end the
list of legacy items that are not implemented. Do not accept anything (`[x]` is
Antti's). Change only `TASKS.md` and `docs/tasks/`.

Acceptance: every issue of both groups appears in the table; the moves follow the
tracker rules; the steward can turn the table into one bulk decision line for
Antti.
