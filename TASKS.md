# Issue tracking for Filemill

Rules for TASKS.md usage are at the bottom of the file.

## Ordered backlog

- Get rid of duplicate vendored code. Simply use the same source files for ui/
  and server/.
- Use one shared client side implementation for rendering Markdown fenced code
  blocks.
- Full file highlighting: don't clip at 8000 chars. Beyond what size should we
  really avoid highlighting in one go, and do it in slices on scroll instead?

## In progress


## Completed

- Plaintext preview doesn't use all vertical space in preview column.
  The whole column should scroll, not just the preview area. [*]
- Syntax highlighting missing in preview pane. Use client side highlighting to maximize
  shared code between ui/ and server/. [*]
- Edit mode for text files in the preview pane [*]
- Remove `dl.meta` section (Where/Size/Modified) from preview pane [*]
- In the cogwheel menu, there's an empty `PREVIEWS` section [*]
- Verify and refine TASKS.md rules [*]

[*]: TASKS.md

---

## Rules

Here are the rules for TASKS.md usage:

### TASKS.md maintenance sessions

- Each backlog item must have either
  - a numbered reference-style link (e.g. `[1]`) to a description file, or
  - `[*]` to indicate no description file is needed for a simple task.
- Link references are listed between `## Completed` and `## Rules`.
- If any issue is missing a link:
  - Create the first missing numbered description file in
    docs/tasks/<NNN-issue-description>.md and add the link

### Modifying issues

- Ensure dependencies between issues are correctly updated.
- State dependencies using
  - indented `- Depends on: [NNN]` bullets in TASKS.md, and
  - YAML frontmatter in description files.
- Ensure backlog order respects dependencies.

### Workflow for new issue completion

- Pick the first backlog issue with no dependency to any uncompleted issue.
- Move it to `In progress` in `main` branch.
- Create or update, review and refine a plan in
  docs/tasks/<NNN-issue-description>.md in `main` (skip for `[*]` items).
- Commit description file (if any) and TASKS.md in `main`.
- From now on, ensure worktree feature branch is always rebased on `main`.
- Implement the plan, and lint, test, review and refine the implementation in
  the worktree feature branch.
- Merge the rebased branch on `main`, and remove the worktree and branch.
- Move the issue to `Completed` in TASKS.md and commit.
