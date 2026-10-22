# Instructions for coding agents

Issues and completion rules are in [TASKS.md](TASKS.md).

`https://filemill.vempai.men/` is a Filemill demo instance.

## Working on the code base

Always do red-green TDD. Every bug must have a failing test first.

Read [docs/ARCHITECTURE-SUMMARY.md](docs/ARCHITECTURE-SUMMARY.md) first,
then the sections of [docs/ARCHITECTURE-REVIEW.md](docs/ARCHITECTURE-REVIEW.md)
that the issue touches, found by heading. Align changes with the review's
proposed architecture and stay within the current issue's scope. Update
affected findings, and their lines in the summary's section index, when the
implementation changes their status.

Use [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests and the quality gate.
It links to browser prerequisites and the separate native checks. Follow its
same-commit documentation rule and the architecture review's ADR rule.
