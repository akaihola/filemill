If an `.md` file contains `<!-- HTML comments -->`, Filemill renders them visible in the preview. They should be hidden.

## Implementation (2026-10-19)

The shared Markdown renderer consumes inline and block comments. Raw HTML
stays disabled. Block comments can contain blank lines and Markdown. An
unclosed block comment hides the rest of its block. Code spans, code blocks
and escaped comment delimiters stay visible. Source and Raw keep the file
bytes. Task checkboxes keep their source line numbers.

See [ADR 0083](../adr/0083-hide-markdown-comments.md).

## Validation

- Red: the static regression failed for `.md` and `.markdown` because inline
  comment text was visible.
- Green: the regression covers inline, block, multiline, unclosed, list and
  block quote comments. It checks code, escaped text, raw HTML, Source and Raw.
- Server browser tests check both extensions and save a task checkbox after a
  multiline comment. They check that hidden comments stay in the saved file.
- Full static validation: 151 passed in each build. Two loader tests failed
  because the Markdown test double lacked the new parser-rule API. The fixture
  now supplies that API. The rich-preview rerun passed all 12 bundle tests.
  The development rerun passed 11 tests; its RST cleanup-count assertion failed
  once and then passed alone. No RST code changed.
- `uvx pre-commit run --all-files`: all seven hooks passed.
- `node ui/core/model/test.mjs`: passed.
- Full server suite with branch coverage: 939 passed; 91% combined coverage.
- Deployment was not run. Local and remote `main` have divergent histories,
  so publishing would require an unrelated history reconciliation.
