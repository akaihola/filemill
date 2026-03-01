# pykofinder Tasks

## How tracking works

- **TASKS.md** (this file) is the session-level scratchpad. Use it to track
  work-in-progress and orient a fresh agent at the start of a session.
- **ISSUES.md** is the authoritative issue registry. Every named issue lives there with
  an explicit `**Status:**` field: `open`, `in-progress`, or `closed`.

**Workflow for an issue:**

1. Pick an issue in ISSUES.md and change its status to `in-progress`.
2. Add a matching `[~]` entry in the **In progress** section below.
3. When done: set `**Status:** closed` and add `**Closed:** YYYY-MM-DD` + `**Prune
after:** YYYY-MM-DD` (closed date + 90 days) in ISSUES.md, then move the entry here
   to **Done** with the same prune-after date in a comment.
4. **90 days after closing:** remove the issue block from ISSUES.md and the `[x]` line
   from Done below.

**Status legend for this file:**
`[ ]` open · `[~]` in-progress · `[x]` done

---

## In progress

_(nothing currently in progress)_

---

## Open

_Items without an issue number are not yet tracked in ISSUES.md._

- [ ] Selected state styling – clicking a `<li>` should add `selected` class to it and
      remove from siblings (requires a small JS snippet or `hx-on::after-request` to
      toggle the class)
- [ ] Pagination for large directories (> 500 entries)
- [ ] Search/filter within a column
- [x] Tooltip for truncated filenames ([#2](ISSUES.md#2--show-full-filename-in-tooltip-when-truncated))
- [ ] Auto-adjust column width to fit longest visible filename ([#3](ISSUES.md#3--auto-adjust-column-width-to-fit-longest-filename))
- [ ] Zoom button to expand preview to full page width ([#4](ISSUES.md#4--zoom-button-expand-preview-to-full-page-width))
- [ ] URL sync and deep-link navigation ([#5](ISSUES.md#5--url-reflects-current-path-deep-link-navigation))
- [ ] Auto-reload on code change – `--live` flag / service unit update ([#6](ISSUES.md#6--auto-reload-on-code-change))
- [ ] Preview unrecognised text files raw – UTF-8 fallback to `<pre>` block ([#7](ISSUES.md#7--preview-unrecognised-text-files-raw))
- [ ] Code file preview (plain text with syntax highlighting)
- [ ] PPTX slide image rendering via LibreOffice (better fidelity than text extraction)
- [ ] Breadcrumb / path display above the columns
- [ ] Keyboard navigation (arrow keys to move between columns)

---

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
- [x] Image preview – PNG, JPEG, GIF, WebP, SVG → `<img>` tag ([#1](ISSUES.md#1--add-png-and-jpeg-preview)) <!-- prune after 2026-05-30 -->
- [x] Move project context from `.claude/CLAUDE.md` to `AGENTS.md` (gitignored) so pi auto-loads it; `.claude/CLAUDE.md` now references `@../AGENTS.md`
