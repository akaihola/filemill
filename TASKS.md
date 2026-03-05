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

- [ ] Pagination for large directories (> 500 entries)
- [ ] Search/filter within a column
- [ ] URL sync and deep-link navigation ([#5](ISSUES.md#5--url-reflects-current-path-deep-link-navigation))
- [ ] Auto-reload: server restart on code change + browser refresh on content change ([#6](ISSUES.md#6--auto-reload-code-changes-restart-server-content-changes-refresh-browser))

- [ ] Keyboard navigation (arrow keys to move between columns) ([#15](ISSUES.md#15--keyboard-navigation))

- [ ] PPTX slide image rendering via LibreOffice (better fidelity than text extraction)

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
- [x] Selected state – `<li>.selected` CSS + click-delegation JS ([#10](ISSUES.md#10--selected-directoriesfiles-must-stay-highlighted)) <!-- prune after 2026-06-03 -->
- [x] Source code syntax highlighting with Pygments "friendly" theme ([#14](ISSUES.md#14--source-code-file-syntax-highlighting)) <!-- prune after 2026-06-03 -->
- [x] Tooltip for truncated filenames ([#2](ISSUES.md#2--show-full-filename-in-tooltip-when-truncated)) <!-- prune after 2026-05-30 -->
- [x] Auto-adjust column width to fit longest visible filename ([#3](ISSUES.md#3--auto-adjust-column-width-to-fit-longest-filename)) <!-- prune after 2026-05-30 -->
- [x] Move project context from `.claude/CLAUDE.md` to `AGENTS.md` (gitignored) so pi auto-loads it; `.claude/CLAUDE.md` now references `@../AGENTS.md` ([#8](ISSUES.md#8--move-project-context-to-agentsmd-for-pi-auto-loading)) <!-- prune after 2026-05-30 -->
- [x] Preview pane always at least 1/3 viewport width ([#9](ISSUES.md#9--preview-pane-always-at-least-13-viewport-width)) <!-- prune after 2026-05-30 -->
- [x] Zoom button to expand preview to full viewport width ([#4](ISSUES.md#4--zoom-button-expand-preview-to-full-page-width)) <!-- prune after 2026-05-30 -->
- [x] Symlink "Access denied." bug – zone-based `_resolve_safe`, pytest dev dep, 16 unit tests ([#11](ISSUES.md#11--symlinks-in-root-denied-with-access-denied)) <!-- prune after 2026-06-03 -->
- [x] `.desktop` link file support – `🔗` icon, `/open-link` redirect, preview card ([#12](ISSUES.md#12--desktop-link-file-support)) <!-- prune after 2026-06-03 -->
- [x] `~/menu/` root – workspace symlinks + `.desktop` hyperlinks; service root changed via drop-in `root.conf`; nixos-config updated <!-- prune after 2026-06-03 -->
- [x] Raw UTF-8 text fallback preview – `<pre class="preview-raw">` for unrecognised extensions (≤256 KB) ([#7](ISSUES.md#7--preview-unrecognised-text-files-raw)) <!-- prune after 2026-06-03 -->
- [x] Breadcrumb navigation – `~ / dir / subdir / file` trail above column strip with OOB swap ([#13](ISSUES.md#13--breadcrumb-navigation)) <!-- prune after 2026-06-03 -->
- [x] Bind address CLI option `--bind` / `-b` with `PYKOFINDER_BIND` env var ([#16](ISSUES.md#16--bind-address-cli-option---bind--serve_bind-env-var)) <!-- prune after 2026-06-03 -->
