# Issue tracking for Filemill

Rules for TASKS.md usage are at the bottom of the file.

## Ordered backlog

- Show version and Git commit hash (if available) via an option in the settings
  menu.
- Fix all test failures. Split into multiple tasks if necessary.
- Full file highlighting: don't clip at 8000 chars. Beyond what size should we
  really avoid highlighting in one go, and do it in slices on scroll instead?
- Get rid of duplicate vendored code. Simply use the same source files for ui/
  and server/.
- Use one shared client side implementation for rendering Markdown fenced code
  blocks. Make sure the implementation flows line-wrapped paragraphs correctly,
  i.e. doesn't insert line feeds in the rendered HTML at each newline in the
  source.
- For highlighted text files (e.g. `.py`, `.js`), the minimum preview width
  isn't currently defined as a static number of characters. So at browser zooms
  >100%, lines are wrapped. Ensure the minimum preview width is 88 characters.
- Pretty-printed and foldable JSON preview, common client side implementation
  for both `server/` and `ui/`.
- Hierarchical view for `.jsonl` files: first level column is a listing showing
  for each line the value of a key which is unique across all lines, preferring
  short or moderate width text values (e.g. `title`, `description`) but using
  scalar values (e.g. `timestamp`, `id`) if none are available. The second
  column is a two-column table view of `(key, value)` pairs for each line. Do
  this entirely on the client side, but following the example of how `.sqlite`
  files are rendered.
- If I navigate deep into
  `~/.bun/install/cache/@agegr/pi-web/0.8.8@@@1/README.md` and return back
  column by column using the left arrow key, the `.bun` column doesn't expand
  when I reach it. It does expand if I navigate to it using the mouse instead.
- make PDF previews full frame just like HTML and Markdown rendered previews

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
    docs/tasks/<N-issue-description>.md and add the link

### Modifying issues

- Ensure dependencies between issues are correctly updated.
- State dependencies using
  - indented `- Depends on: [N]` bullets in TASKS.md, and
  - YAML frontmatter in description files.
- Ensure backlog order respects dependencies.

### Workflow for new issue completion

- Pick the first backlog issue with no dependency to any uncompleted issue.
- Move it to `In progress` in `main` branch.
- Create or update, review and refine a plan in
  docs/tasks/<N-issue-description>.md in `main` (skip for `[*]` items).
- Commit description file (if any) and TASKS.md in `main`.
- From now on, ensure worktree feature branch is always rebased on `main`.
- Implement the plan, and lint, test, review and refine the implementation in
  the worktree feature branch.
- Merge the rebased branch on `main`, and remove the worktree and branch.
- Move the issue to `Completed` in TASKS.md and commit.
- Do any deployment steps if defined in the general development worklow.
