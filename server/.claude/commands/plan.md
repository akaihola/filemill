---
description: Start a TDD implementation plan for an open issue
---

Start work on issue $ARGUMENTS (provide either the issue number, e.g. `#40`, or a short title keyword).

Steps:

1. Read `ISSUES.md` and locate the matching open issue. If the argument is ambiguous, list candidates and stop.
2. Read `CONTRIBUTING.md` to confirm the TDD rules, test conventions, and commit style.
3. Read the relevant source files identified in the issue's implementation sketch.
4. Change the issue's `**Status:**` from `open` to `in-progress` in `ISSUES.md`.
5. Move the issue's entry in `TASKS.md` from **Open** to **In progress** (change `[ ]` to `[~]`).
6. Commit the status change: `git commit -m "docs: start #N – <title>"`
7. Produce a concrete, step-by-step implementation plan:
   - List every file that will change and why.
   - For each logical chunk of work, state: (a) the failing test to write first, (b) the production change to make it pass, (c) the commit message.
   - Flag any open questions or design decisions that need a choice before coding can start.

Stop after producing the plan. Do not write any code yet — wait for explicit approval of the plan before proceeding.
