---
depends-on: [13]
---

# Merge the three extra issue trackers into TASKS.md

## Goal

One issue tracker: root `TASKS.md` and `docs/tasks/`. Roadmap phase 2, step 1.

## Steps

1. Read `server/TASKS.md`, `server/ISSUES.md` and `static/TASKS.md`.
2. For each item that is not done: add one bullet to `## Ordered backlog` in
   root `TASKS.md`. Follow the rules at the end of that file. Use `[*]` when
   two lines are enough. Otherwise create `docs/tasks/<N>-<slug>.md` and use
   `[N]`.
3. For each item that is done: do nothing. Git keeps its text.
4. Delete the three files with `git rm`.
5. Search for links to the deleted files:
   `git grep -n "ISSUES.md\|server/TASKS.md\|static/TASKS.md"`. Fix each link.

## Done when

- `ls server/TASKS.md server/ISSUES.md static/TASKS.md` reports no such file.
- `git grep -n "ISSUES.md"` prints nothing.
- Every open item from the three files appears one time in root `TASKS.md`.

## Scope

`TASKS.md`, `docs/tasks/`, and the three files to delete.
