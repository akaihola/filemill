# Instructions for coding agents

Issues are tracked in `TASKS.md`.

`https://filemill.vempai.men/` is a Filemill demo instance.

## Working on the code base

Always do red-green TDD. Every bug must have a failing test first.

Always read `docs/ARCHITECTURE-REVIEW.md` first. Consider each change you make against
the proposed changes. Don't do anything that contradicts the proposed end state of the
architecture. Make sure your changes align with the proposed architecture, and take a
step towards it if possible. However, don't do architecture changes in parts of the code
base beyond the scope of the current task. Other tasks will take care of those changes.
Keep `docs/ARCHITECTURE-REVIEW.md` up to date with the state of the code base.
