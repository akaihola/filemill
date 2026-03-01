# pykofinder Tasks

## Done

- [x] `pyproject.toml` – project metadata, deps, entry point
- [x] `src/pykofinder/__init__.py` – package marker
- [x] `src/pykofinder/styles.py` – CSS (Finder column view) + Pygments + HTMX scroll JS
- [x] `src/pykofinder/rendering.py` – markdown-it-py instance with all mdit-py-plugins
- [x] `src/pykofinder/preview.py` – `render_preview()` dispatcher (md/docx/pptx/pdf)
- [x] `src/pykofinder/columns.py` – `list_column()`, `initial_columns()`, column pruning JS
- [x] `src/pykofinder/app.py` – FastHTML app, `GET /`, `GET /click`, `GET /raw`, `_resolve_safe()`
- [x] `src/pykofinder/cli.py` – Typer CLI with `--port`, `--live`, ROOT env-var for reload mode
- [x] `uv sync` – all 43 packages installed, smoke test passed

## Open

- [ ] Selected state styling – clicking a `<li>` should add `selected` class to it and remove from siblings (requires a small JS snippet in the column or HTMX `hx-on::after-request` to toggle the class)
- [ ] Pagination for large directories (> 500 entries)
- [ ] Search/filter within a column
- [ ] Image preview (`.png`, `.jpg`, `.gif`, `.svg` → `<img>` tag)
- [ ] Code file preview (plain text with syntax highlighting)
- [ ] PPTX slide image rendering via LibreOffice (better fidelity than text extraction)
- [ ] Breadcrumb / path display above the columns
- [ ] Keyboard navigation (arrow keys to move between columns)
