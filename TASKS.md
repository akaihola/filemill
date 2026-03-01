# pykofinder Tasks

Bugs and feature requests are tracked in [ISSUES.md](ISSUES.md).

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
- [ ] Image preview – PNG, JPEG, GIF, WebP, SVG → `<img>` tag ([#1](ISSUES.md#1--add-png-and-jpeg-preview))
- [ ] Tooltip for truncated filenames ([#2](ISSUES.md#2--show-full-filename-in-tooltip-when-truncated))
- [ ] Auto-adjust column width to fit longest visible filename ([#3](ISSUES.md#3--auto-adjust-column-width-to-fit-longest-filename))
- [ ] Zoom button to expand preview to full page width ([#4](ISSUES.md#4--zoom-button-expand-preview-to-full-page-width))
- [ ] Code file preview (plain text with syntax highlighting)
- [ ] PPTX slide image rendering via LibreOffice (better fidelity than text extraction)
- [ ] Breadcrumb / path display above the columns
- [ ] Keyboard navigation (arrow keys to move between columns)
