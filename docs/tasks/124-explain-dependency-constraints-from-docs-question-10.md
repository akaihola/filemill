# Explain dependency constraints from docs question 10

Source: [the docs check], question 10.
Proposed by [the plain-answer task]; approved by the user on 2026-10-20
(question 10). Label: `steward`.

## Recommendation

Clarify the policy and add evidence-based comments without changing dependency versions.

## Work

1. Distinguish minimum supported versions, deliberate bounded versions and exact lockfile selections in [GOALS].
2. Explain the build-backend range and conditional zstandard dependency where history or validation supports a reason; preserve the Playwright browser-match and mypy notes.
3. Check inherited development minimums against history. State when their compatibility rationale is unverified; do not claim minimum-version testing or invent a reason for every inherited floor.

## Acceptance

Every described reason has evidence or an explicit gap. No version specifier or lock resolution changes, no blanket pinning is added, and the server docs tests pass.

## Implementation, 2026-10-20

- **Policy:** [GOALS] separates declared support floors, bounded versions and
  exact [lockfile] selections. A declared minimum is not proof of testing at
  that version. Unknown compatibility reasons are explicit gaps.
- **Build backend:** `26d515b9` introduced `uv_build>=0.6.6,<0.7` in the
  initial project. `e01a40b4` retained it when moving the server package.
  Neither change explains the endpoints. [Server dependency comments] state
  what the range permits without claiming a compatibility failure or a
  minimum-version test.
- **Archive compatibility:** `b91a3d8c` added the conditional zstandard
  dependency. The [archive provider] uses `compression.zstd` on Python 3.14+
  and the third-party package on older interpreters. The `0.23` floor's
  compatibility rationale remains unverified. `f26da085` added the development
  dependency for mypy's compatibility-import check, including on Python 3.14;
  that comment is preserved.
- **Development floors:** `eec53713` records pytest, httpx and pytest-cov
  floors; `e01a40b4` carried them into the server package. `3b9ca9d1` added
  Ruff and mypy, `2a9944c3` added PyYAML for CI checks, and `587752b4` added
  pytest-asyncio during the static pytest migration. These changes establish
  tool use, but do not establish why those specific minimum versions are
  necessary. The comments mark their compatibility rationale and testing at
  the minimum versions as unverified. [Workspace dependency comments] point
  to the server evidence rather than inventing separate reasons.
- **Browser matching:** `c8355929` records browser-launch failures when the
  Playwright package and managed browser revisions differ. `875b032b` records
  the later adjustment to the managed bundle. The existing browser-match
  comment is preserved. The lock selects an exact release within the declared
  compatible-release range.

## Validation, 2026-10-20

- **Red then green:** the new [server docs test] failed because the old policy
  did not distinguish floors from bounded versions and lock selections. All
  22 server docs tests then passed with `uv run --project server pytest -q
  server/tests/test_docs.py`.
- **No dependency changes:** parsed TOML before and after is equal for both
  project files. The lockfile has no diff. No specifier or resolution changed.
- **Repository gate:** all eight hooks passed with
  `uvx pre-commit run --all-files`. Relative reference-link targets exist and
  `git diff --check` passed. The full browser suites were not run for this
  documentation and comments change.

[the docs check]: 109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md#questions
[the plain-answer task]: 115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md
[GOALS]: ../GOALS.md
[lockfile]: ../../uv.lock
[server dependency comments]: ../../server/pyproject.toml
[workspace dependency comments]: ../../pyproject.toml
[archive provider]: ../../server/src/filemill/providers/archive.py
[server docs test]: ../../server/tests/test_docs.py
