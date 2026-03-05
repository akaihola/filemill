# Contributing to pykofinder

## Project context

pykofinder is a **macOS Finder-style column-view file browser and previewer**,
served as a FastHTML web application. Directories are navigated by clicking
column entries; files are previewed inline (Markdown, DOCX, PPTX, PDF, images,
plain text, code with syntax highlighting).

### Source layout

```
src/pykofinder/
├── app.py          # FastHTML app, routes, _resolve_safe()
├── cli.py          # Typer CLI entry point
├── columns.py      # Column HTML generation + pruning JS
├── preview.py      # Preview dispatcher (md / docx / pptx / pdf / img)
├── rendering.py    # markdown-it-py instance with plugins
└── styles.py       # CSS + Pygments theme + HTMX scroll JS

tests/
├── conftest.py     # Shared fixtures (tmp dirs, test client)
├── test_app.py     # Route-level integration tests
├── test_columns.py # Column HTML generation
├── test_preview.py # Preview rendering
├── test_rendering.py  # Markdown pipeline
├── test_resolve_safe.py  # Path-safety logic
└── test_cli.py     # CLI smoke tests
```

### Key invariants

- All routes are under a configurable `ROOT` directory; `_resolve_safe()` in
  `app.py` enforces that no path escapes that root (symlinks included).
- Column pruning is done client-side via a small `<script>` injected into each
  click response – no server round-trip needed.
- HTMX drives all dynamic updates; there is no JavaScript build step.

---

## Development rules

- **TDD (red-green)** – write a failing test first, then make it pass; never
  write production code without a failing test driving it.
- **Full test coverage** – every new or changed behaviour must be covered by
  tests. Unit/integration tests use pytest; UI tests use the `playwright`
  Python package pinned to the version in `$UV_CONSTRAINT`
  (currently `playwright==1.57.0`).
- **Documentation stays current** – update `README.md`, `ISSUES.md`, and
  `TASKS.md` as part of every change, not as an afterthought.
- **Simplify aggressively** – look for opportunities to simplify and gain
  elegance on every pass; less code is usually better code.
- **Frequent conventional commits** – commit at every logical checkpoint using
  the conventional-commit prefixes: `feat:`, `fix:`, `test:`, `docs:`,
  `refactor:`, `chore:`, `style:`, `perf:`.

## Running tests

```bash
uv sync
uv run pytest                  # unit + integration (with coverage)
uv run pytest tests/ui/        # Playwright UI tests
```

## Submitting changes

1. Open an issue in `ISSUES.md` and set its status to `in-progress`.
2. Add a matching `[~]` entry in `TASKS.md`.
3. Work in a feature branch; follow the TDD cycle above.
4. Update docs and mark the issue closed before merging.
