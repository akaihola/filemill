# Instructions for coding agents

Issues and completion rules are in [TASKS.md](TASKS.md).

`https://filemill.vempai.men/` is a Filemill demo instance.

## Working on the code base

Always do red-green TDD. Every bug must have a failing test first.

Read [docs/ARCHITECTURE-REVIEW.md](docs/ARCHITECTURE-REVIEW.md) first. Align
changes with its proposed architecture and stay within the current issue's
scope. Update affected findings when the implementation changes their status.

Use [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests and the quality gate.
It links to browser prerequisites and the separate native checks. Follow its
same-commit documentation rule and the architecture review's ADR rule.
