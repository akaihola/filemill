# Contributing to Filemill

## Setup

Filemill has a static edition and a server edition. Read the [root
README](README.md) for the project layout and links to each edition.

For the server edition:

```bash
cd server
uv sync
```

Edit shared UI files through `ui/`. The root `ui/` path points to the server
package directory.

## Tests

Run the server tests with:

```bash
cd server
uv run pytest
```

Run the static checks with:

```bash
cd static
./build-index.py --check
uv run --with "playwright==1.61.0" python3 test-ui.py
uv run --with "playwright==1.61.0" python3 test-url.py
uv run --with "playwright==1.61.0" python3 test-rich.py
```

Run `pre-commit run --all-files` before you commit. It runs the Python and UI
formatters and linters, the type checker, and the static bundle check.

## Commits

Use a Conventional Commit prefix. Examples include `feat:`, `fix:`, `test:`,
`docs:`, `refactor:`, `chore:`, `style:`, and `perf:`. Keep each commit to one
logical change. Update documentation in the same commit as the change.

## Writing

Write Markdown in ASD-STE100 Simplified Technical English. Use short sentences,
common words, active voice, and one instruction per step. Define a technical term
before you use it. Keep links relative when the target is in this repository.
