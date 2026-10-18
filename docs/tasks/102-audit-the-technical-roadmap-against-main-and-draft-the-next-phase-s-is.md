---
depends-on: [101]
---

# Audit the technical roadmap against main and draft the next phase's issues

Steward issue, 2026-10-18. Goal: agentic-leverage (filemill is a tier-1
project in `<steward-vault>/Goals.md`). filemill's Ordered
backlog and Unverified proposals are empty, while `docs/ROADMAP.md` lays out
nine phases, each "small enough for one task", with "Done when" checks.
Nothing records which phases are done since [25], [87], [93], [99] and
others landed. This issue gives the steward the next filemill backlog to
file.

It depends on [101], the browser-test issue, only so that two filemill worktrees
are not created at once: a Claude worker's sandbox holds a lock in the
shared `.git/`, and T3 then cannot create a second worktree.

## Work

1. For each phase and each numbered step, decide done, partly done or open
   on today's `main`, and cite the commit, issue, ADR or file that shows it.
   Run the cheap "Done when" checks (greps, line counts,
   `pre-commit run --all-files`). For test-suite checks, cite the recorded
   runs in [99], [100] and [101] instead of rerunning the
   full suites.
2. Note the steps the code has overtaken (for example ADR 0067 for Phase 0
   step 2) and any that no longer fit `docs/GOALS.md`.
3. For the first phase that is not done and the one after it, draft issue
   texts in this file: title, goal, work, ground rules and acceptance, each
   sized for one agent run of about an hour, split where a phase is larger.
   Name the questions Antti must answer before a draft can start.
4. Propose status annotations for `docs/ROADMAP.md` as a patch in this
   file. Don't apply it.

## Ground rules

- Change only this description file and the issue's tracker moves.
- Don't push, deploy or restart services.

## Acceptance

- A table of every phase and step with status and evidence.
- Draft issues for the next two open phases, with their open questions.
