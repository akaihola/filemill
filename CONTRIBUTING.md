# Contributing to Filemill

## Setup

Filemill has a static edition and a server edition. Read the [root
README](README.md) for the project layout and the link to each edition.

Set up the server edition:

```bash
cd server
uv sync
```

Edit shared UI files through `ui/`. The root `ui/` path is a symlink into the
server package.

## Model boundary

Keep browser APIs out of `ui/core/model/`, including its imports. Pass measured
sizes and plain key data into model functions. Keep element creation, event
listeners and rendering effects in the browser modules beside it. Both entry
points use the same model. Run its dependency-free checks with
`node ui/core/model/test.mjs` or
`deno run --allow-read=ui/core/model ui/core/model/test.mjs`.

## Markdown previews

Keep source highlighting in `ui/core/markdown-source.js`. Preserve each source
character and keep links inside code inactive. Both Markdown preview modes use
`ui/core/markdown-links.js` for destination validation and path resolution. Test
link behavior with the real vendored Markdown renderer, not a loader stub.

## Tests

Run the server tests:

```bash
cd server
uv run pytest
```

Run the automated static checks from the repository root. These include the
UI, URL, rich preview, RST, model and PWA checks. `static/test-e2e.py` remains a
manual test that requires folder selection and terminal input. Do not collect it
as an automated browser test.

Run the static checks:

```bash
static/build-index.py --check
uv run --project server pytest static
uv run --project server pytest static --dev
```

Run `pre-commit run --all-files` before you commit. It runs the Python and UI
formatters and linters, the type checker, and the static bundle check.

## Commits

Use a Conventional Commit prefix: `feat:`, `fix:`, `test:`, `docs:`,
`refactor:`, `chore:`, `style:` or `perf:`. Keep each commit to one logical
change. Update the documentation in the same commit as the change.

## Writing

Write Markdown in ASD-STE100 Simplified Technical English. Use short sentences,
common words, the active voice, and one instruction per step. Define a technical
term before you use it. Use a relative link when the target is in this
repository.
