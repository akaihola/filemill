# Issue tracking for Filemill

Rules for TASKS.md usage are at the bottom of the file.

## Unverified proposals

- [*] From documentation, docstrings and comments, remove references to specific
  development setups which include e.g. server names and local paths.

## Ordered backlog

- [29] Make `ui/core/` a model package with no DOM: nodes, selection, folding
  arithmetic, keyboard map and deep links. Keep a thin DOM renderer beside it.
    - Depends on: [21]

- [30] Prototype one native shell that hosts the DOM renderer in a WebView and supplies
  the three ports natively. Choose the smallest binary that passes `test-ui.py`.
    - Depends on: [29]

- [31] Evaluate AppKit, GTK and WinUI against the WebView prototype. Record the
  comparison in an ADR. Do not start a native toolkit before the ADR exists.
    - Depends on: [30]






- [*] Feature: Clicking on a content search result now opens the raw file. Open the
  rendered file in the UI preview pane instead.


## Scheduled
- [64] Keep subfolder and folded parent widths stable during Up/Down navigation.
- [42] Fix the extra mount prefix in rendered `~/...` Markdown links.
- [41] Fix plain-text reStructuredText previews in Source and Rendered modes.
- [40] Return preview focus to the containing folder and selected file.
- [38] Fix PPTX previews that show unspaced slide text in both modes.

- [*] Treat `.py.j2` as Python.

## In Progress

- [39] Fix Back/Forward navigation across folders, previews and raw files.

- [*] Delete `providers/json_provider.py`, `providers/csv_provider.py` and their
  registration in `vfs.py`. JSON is a browser virtual filesystem. CSV comes in phase 8.

- [*] Default `--bind` in `server/src/filemill/cli.py` to `127.0.0.1`. Document it in
  `SECURITY.md`.

- [*] Replace every `wait_for_timeout` in `static/*.py` and `server/tests/` with
  `wait_for_function` or `expect`. Done when `grep -r wait_for_timeout` finds nothing.

- [43] Investigate the 11 server browser failures also reproduced on main.

- [*] Clarify the meaning of `[~]` in this file. Review Kandev task sessions to find out
  what it means.

- [*] Keep `static/test-e2e.py` as a manual check. Describe when and how to run it in
  `static/FSA-TEST-CHECKLIST.md`.

- [25] Move `static/test-ui.py`, `test-url.py` and `test-rich.py` under pytest with
  fixtures for the fake handle, the OPFS root and the bundle. Split `main()` by section.
    - Depends on: [12]

- [*] `.py` files are not highlighted at all.

## Completed

- [*] Delete `_document_page` — document representations, including `layout=no-columns`,
      now return the shared client shell.

- [13] Correct the stale claims that review finding 15 lists in `server/README.md`,
      `server/CONTRIBUTING.md`, `server/TASKS.md`, `docs/tasks/2-*.md` and root
      `TASKS.md`.

- [*] Split `applyScroll` in `ui/core/layout.js` into `foldFromScroll`, `applyWidths`,
      `panFocus` and `slideTail`. Each function is under 25 lines.

- [15] Split the decisions table in `static/AGENTS.md` into one dated ADR file per
  decision in `docs/adr/`. Each file has context, decision, measurement, consequences.

- [10] Toggling `Source` / `Rendered` reloads the whole page and causes an uncomfortable
  blink and a delay. Just the preview pane should be reloaded, and the URL and history
  updated.

- [*] Delete the `/raw?path=` route in `app.py`. The client builds `${API}/raw?p=` URLs
  for images, PDF and HTML. Done when `grep -r raw?path server/src` prints nothing.
    - Depends on: [33]

- [*] Virtualise column rows. `content-visibility` made layout cheap, but a 100 k-entry
  directory still builds 100 k DOM nodes. Do this only if such folders show up.

- [*] Expand `~/path` links in rendered Markdown to the mount that resolves to `$HOME`.
  Today `[text](~/note.md)` is a dead link although the file exists.

- [6] Centralize file-kind classification across filesystem producers and preview/edit
  consumers. Add one test table per language that both sides share.

- [44] Document demo instances matching each browser test setup.

- [*] Delete `/open-link` and `_parse_desktop_url` in `app.py`. `desktopCard` in
  `ui/adapters/preview-local.js` already handles `.desktop` files in both editions.

- [*] Give each magic number in `ui/core/state.js`, `layout.js`, `nav.js`, `render.js` a
  name and a one-line comment that says why the value is what it is.

- [21] Cache the preview element keyed on the previewed node and its `meta`, the same
  way `colCache` keys columns. A resize must cause zero `PREVIEW.render` calls.

- [*] Delete `/sse/reload` and `LIVE_MODE` in `app.py`, `LIVE_RELOAD_JS` in `styles.py`
  and the `watchfiles` dependency. Delete their tests.

- [*] For hierarchical nested view of JSON, don't use the folder icon. Use the JSON icon for
  the whole file, and `{}` and `[]` icons for objects and arrays.

- [*] Run the static and server browser tests through one root `conftest.py` and one
  Playwright fixture. Delete the CDN proxy plumbing in `test_browser_keyboard.py`.
    - Depends on: [25]

- [*] Add a preview for `.mp4` files with a `<video controls>` element, as one registry
  entry plus one test.
    - Depends on: [26]

- [*] Implement CSV as a browser virtual filesystem in `ui/adapters/vfs-csv.js`, like
  JSONL: one entry per row, a key/value preview per row. No Python.
  Closes legacy server issue #49.
    - Depends on: [26]

- [*] Compute the symlink zone map one time per request in `paths.py`. Delete the three
  other walks of the root that build the same map.
    - Depends on: [24]

- [*] Stop `server/tests/conftest.py` from changing the module global `ROOT`. Done when
  `uv run pytest -n auto` passes at the repository root.

- [*] Replace `python-fasthtml` with `starlette` and `uvicorn`. The shell becomes one
  string template. Done when `dependencies` has starlette, uvicorn, typer, python-pptx.
    - Depends on: [24]

- [*] On mobile, long-pressing a file or directory should open a menu of actions to copy
  its base name, relative path or absolute path.

- [*] Delete `server/src/filemill/styles.py`. The shell links `/ui/core/styles.css`, and
  no other server route emits HTML. Delete the tests that pin `APP_CSS`.
    - Depends on: [33], [34]

- [*] Delete `/api/render` in `app.py`, `render_upload` in `api.py` and
  `ui/adapters/preview-upload.js`. Local folders in the server edition use PreviewRich.
    - Depends on: [32], [34]

- [*] Each row of a JSONL file must be presented exactly like a hierarchical nested view
  of a JSON file.

- [45] Show JSON children beside a foldable preview of the selected value.

- [46] Fix ancestor columns unfolding during down-arrow navigation.

- [*] Keyboard navigation using arrows still doesn't animate folding/unfolding/resizing of
  columns. Do systematic debugging to identify the cause, and fix it.

- [7] Make entry ordering an adapter-owned contract.
    - Depends on: [6]

- [47] Fold folder columns on preview entry and restore the containing column on exit.

- [48] Keep ancestor folding unchanged during Up/Down navigation.

- [*] Add a PWA manifest and service worker to the static bundle so `static/index.html`
  installs as a standalone window. The server edition already serves `/manifest.json`.

- [49] Fix content search errors and restrict search to the focused directory tree.

- [*] The `Fullscreen` button in the preview pane doesn't do anything. No errors seen on the
  JavaScript console either.

- [50] Fix missing reStructuredText rendering and highlighting after the initial
  implementation.

- [51] Return raw file bytes for URLs without query parameters.

- [52] Return focus to the parent column when leaving the preview with ArrowLeft.

- [*] Remove every `# noqa: S608` in `server/src/filemill/providers/sqlite.py`. Quote
  identifiers with `"` and replace `"` inside them with `""`, or check `sqlite_master`.

- [53] Let Markdown paragraphs wrap to the preview width instead of preserving
  linefeeds.

- [*] Typing a right arrow when the rightmost column before the preview is focused
  should focus the preview and let the user scroll it up/down using the arrow and
  PgUp/PgDn keys.

- [*] Delete `static/hotreload.py`, `forgetRoots` in `ui/adapters/storage.js`, and
      `PYGMENTS_FORMATTER` and the second `FRIENDLY_CSS` in
      `server/src/filemill/styles.py`.

- [54] Keep all Markdown previews within the portrait screen width.

- [55] Fix the favicon 404 and `renderPage is not a function` error.

- [*] In `ui/adapters/vfs-json.js`, merge `withJsonl` and `withJson` into `withVirtual`,
  and `withJsonlPreview` and `withJsonPreview` into `withVirtualPreview`.

- [20] Create `ui/core/limits.js` with one `TEXT_MAX` and one image extension list.
  Create one `mountRoot()` and one `currentPath()`. Delete the copies and `pathParts`.

- [22] Replace `cursor[i]`, `sel[i]` and `node.lastSel` with one selection model:
  `sel[i]` is the selected name. Derive the row index when needed.

- [*] Add root `CONTRIBUTING.md` (setup, tests, commit style, STE rule), `SECURITY.md`
  (threat model, how to report) and `CHANGELOG.md` (Keep a Changelog format).

- [*] Document the full port contract in `ui/core/ports.js`: `FS.node`, `FS.blob`,
  `ROUTER.write(state, replace)`, `RouterPath.base` and every node field.

- [*] Delete `server/PLAN-18.md`, `PLAN-19.md`, `PLAN-20-shared-frontend.md` and
  `server/lmt/`. Move a paragraph only if it is still true and is not elsewhere.

- [*] Make root `README.md` the one explanation of the two editions and their ports.
  `server/README.md` and `static/AGENTS.md` link to it and keep edition-specific text.

- [*] Delete `server/.pi/settings.json`, `server/mobile-narrow-preview.png`,
  `server/.claude/commands/` and `architecture-review-20260904.html`.

- [56] Add a Rendered / highlighted Source toggle beside Raw and Fullscreen.

- [*] Add `.pre-commit-config.yaml` with ruff, ruff-format, mypy, deno fmt, deno lint
  and `static/build-index.py --check`. Run `pre-commit run --all-files` until it passes.

- [57] Fix portrait horizontal overflow potentially caused by the fold hint.

- [*] Feature: ability to delete a file or a directory from the file manager.

- [*] Feature: Syntax highlight Markdown and HTML files in the `?filemill=highlight`
  view.

- [58] Preserve preview mode in file URLs so Back from Raw restores the finder.

- [59] Fix the missing-timestamp error for YouTube WebVTT files.

- [*] In an installed PWA, there is no way to get back from raw file view to the file
  manager view.

- [60] Fix content searches failing with `Search timed out`.

- [61] Choose unique CSV row keys and keep duplicate values independently selectable.

- [37] Evaluate hybrid Python/Jinja highlighting and report supported alternatives.

- [62] Prevent further left swipes from exposing a margin beside a fullscreen portrait
  preview.

- [*] Add `deno fmt` and `deno lint` for `ui/` (one pinned binary, no Node project).
  Format `ui/` one time and commit the result as its own commit.

- [*] Add `ruff` and `mypy` to the `dev` group in `server/pyproject.toml`. Add
  `[tool.ruff]` with `line-length = 88`. Fix all findings. Run `ruff format`.

- [63] Add Raw, Source / Rendered and Fullscreen controls to the preview toolbar.

- [12] Make `static/test-ui.py` run to its end, then fix the three checks that fail: the
  `.pv-content` timeout and the two "edit starts at the top" checks.

- [*] In `ui/core/state.js`, replace `node.jsonl ? kids : sortKids(kids)` with a
  `node.ordered` flag. Each virtual provider (JSON, JSONL, SQLite) sets the flag.

- [28] Grow the editor behind the `FS.write` port: undo, find, a line gutter and a
  "modified" mark. Each addition is one file in `ui/editor/`.

- [27] Try reStructuredText rendering in the browser with Pyodide or a WASM tool, behind
  the rich renderer consent switch. Record size and first-load time in an ADR.
    - Depends on: [26]

- [*] Render `.pptx` in the browser: unzip the file and show the slide text, as one
  registry entry. Then delete `_preview_pptx`, `python-pptx` and `/api/preview`.
    - Depends on: [26]

- [24] Reduce `app.py` to routing: move `_resolve_safe` and the symlink map to
  `paths.py` and the PWA routes to `pwa.py`. No imports inside functions.
    - Depends on: [33], [34]

- [33] Keep the URL contract, drop the server-side representations: the server sends
  bytes for `?filemill=raw` and the shell for all else. The client renders the view.
    - Depends on: [32]

- [35] Decide the fate of the `/w/` named mounts and their CORS middleware: delete them,
  or make CORS opt-in and document it in `SECURITY.md`.
    - Depends on: [32]

- [32] Render Markdown and `.docx` in the browser in the server edition too. Serve the
  pinned renderer modules from `ui/vendor/`. Then delete `rendering.py` and its deps.

- [34] Make the SQLite provider return JSON only. The client renders tables and rows
  with the JSON hierarchical view. Delete the HTML in `providers/sqlite.py`. Close [9].

- [9] Close the conditional `ViewSpec` proposal: [34] removed the six-argument interface.

- [26] Create one renderer registry, a list of `{kind, render, fallback}`. Both editions
  fill it from the same core list plus their own adapters.

- [36] Decide how the installed PWA gets a running server: a systemd or launchd unit, a
  launcher, a desktop shell, or only a better "server not running" page.

- [*] Add a `LICENSE` file with the MIT license text. `README.md` already says MIT. Use
      the current year and "Antti Kaihola" as the copyright holder.

- [*] Feature: Move to using `pptx-vanilla-viewer` from a CDN for previewing PowerPoint
  files. Current PPTX support was implemented in task
  38ab06e2-c607-4d4a-9978-67847e70d27d.

## Accepted

[6]: docs/tasks/6-file-kind-classification.md
[7]: docs/tasks/7-adapter-owned-entry-order.md
[9]: docs/tasks/9-vfs-viewspec.md
[10]: docs/tasks/10-preview-mode-toggle.md
[12]: docs/tasks/12-test-ui-runs-to-end.md
[13]: docs/tasks/13-correct-stale-documents.md
[15]: docs/tasks/15-split-decisions-into-adrs.md
[20]: docs/tasks/20-one-limits-one-path.md
[21]: docs/tasks/21-cache-preview-element.md
[22]: docs/tasks/22-one-selection-model.md
[24]: docs/tasks/24-split-app-py.md
[25]: docs/tasks/25-static-tests-under-pytest.md
[26]: docs/tasks/26-renderer-registry.md
[27]: docs/tasks/27-rst-in-browser.md
[28]: docs/tasks/28-editor-features.md
[29]: docs/tasks/29-core-without-dom.md
[30]: docs/tasks/30-webview-shell.md
[31]: docs/tasks/31-native-toolkit-evaluation.md
[32]: docs/tasks/32-browser-markdown-in-server-edition.md
[33]: docs/tasks/33-shell-for-every-representation.md
[34]: docs/tasks/34-sqlite-json-only.md
[35]: docs/tasks/35-decide-web-mounts.md
[36]: docs/tasks/36-pwa-start-server.md
[37]: docs/tasks/37-py-j2-highlighting.md
[38]: docs/tasks/38-pptx-rendered-preview.md
[39]: docs/tasks/39-browser-history-navigation.md
[40]: docs/tasks/40-preview-return-containing-folder.md
[41]: docs/tasks/41-rst-rendering-regression.md
[42]: docs/tasks/42-tilde-link-mount-prefix.md
[43]: docs/tasks/43-server-browser-baseline-failures.md
[44]: docs/tasks/44-browser-test-demo-instances.md
[45]: docs/tasks/45-json-selected-value-preview.md
[46]: docs/tasks/46-down-arrow-ancestor-unfolding.md
[47]: docs/tasks/47-preview-focus-folding.md
[48]: docs/tasks/48-preserve-ancestor-fold-state.md
[49]: docs/tasks/49-content-search-scope.md
[50]: docs/tasks/50-rst-rendering-first-regression.md
[51]: docs/tasks/51-raw-url-redirect.md
[52]: docs/tasks/52-preview-left-arrow-focus.md
[53]: docs/tasks/53-markdown-paragraph-wrapping.md
[54]: docs/tasks/54-portrait-markdown-width.md
[55]: docs/tasks/55-favicon-deeplink-error.md
[56]: docs/tasks/56-rendered-source-toggle.md
[57]: docs/tasks/57-portrait-fold-hint-overflow.md
[58]: docs/tasks/58-raw-history-preview-mode.md
[59]: docs/tasks/59-youtube-webvtt-timestamps.md
[60]: docs/tasks/60-content-search-timeout.md
[61]: docs/tasks/61-csv-unique-row-keys.md
[62]: docs/tasks/62-portrait-preview-swipe-overflow.md
[63]: docs/tasks/63-preview-toolbar-controls.md
[64]: docs/tasks/64-column-width-stability.md
[*]: TASKS.md

---

## Rules

Here are the rules for TASKS.md usage:

### TASKS.md maintenance sessions

- Each backlog item must be prefixed with either
    - a numbered reference-style link (e.g. `[1]`) to a description file, or
    - `[*]` to indicate no description file is needed for a simple task.
- Link references are listed between `## Completed` and `## Rules`.
- Keep summaries concise. Move detailed requirements, rationale, examples and
  acceptance criteria into `docs/tasks/N-issue-description.md`; preserve simple
  tasks inline. Reuse an existing description for the same issue.
- For a new description, use the first unused number, checking both this file and
  description filenames in Git history. Do not reuse numbers of accepted issues.
- The section in this file records status. Completed descriptions retain historical
  requirements, paths and validation results; they are not current implementation
  instructions. Date later corrections and distinguish regressions from earlier work.
- Any completed tasks which haven't yet been moved from `## In Progress` to
  `## Completed` should be moved there.
- Any in progress tasks which haven't yet been moved from `## Ordered backlog` or
  `## Scheduled` to `## In Progress` should be moved there.
- Remove all issues the user has moved to the `## Accepted` section along with any
  related description files in `docs/tasks/` and the reference-style links pointing to
  them.
- Ensure there are no duplicate sections, and that they are in the correct order:
  `## Unverified proposals` -> `## Ordered backlog` -> `## Scheduled` ->
  `## In Progress` -> `## Completed` -> `## Accepted` -> `## Rules`.

### Modifying issues

- Ensure dependencies between issues are correctly updated.
- State dependencies using
    - indented `- Depends on: [N]` bullets in TASKS.md, and
    - YAML frontmatter in description files.
- Ensure backlog order respects dependencies.
- When you move an issue to a different section, move its lines without a change. Keep
  the prefix, the bullet text and the line wrapping the same. Git can then see the move,
  and concurrent moves do not cause a conflict.

### Workflow for new issue completion

1. Choose issue and schedule work (typically by a heartbeat)

- Pick the first backlog issue with no dependency to any uncompleted issue.
- Move it under `## Scheduled` in `TASKS.md` and remove it from `## Ordered backlog` in
  the `main` branch and commit.

2. Work on the issue (typically by a task workflow)

- Move the issue under `## In Progress` in `TASKS.md` in the worktree branch, ensure
  it's not in `## Ordered backlog`, and commit.
- Create or update, review and refine a plan in docs/tasks/<N-issue-description>.md in
  `main` if more description is needed than nicely fits in a bullet point. If you
  created a plan document, link to it using a new `[N]` reference-style link.
- Commit description file (if any) and TASKS.md in `main`.
- Rebase the worktree feature branch on `main` before moving the issue, and keep it
  rebased afterwards.
- Implement the plan, and lint, test, review and refine the implementation in the
  worktree feature branch.

3. Merge and deploy (typically by last steps of a task workflow)

- Merge the rebased branch on `main`, and remove the worktree and branch.
- Move the issue from `## In Progress` to `## Completed` in TASKS.md and commit.
- Do any deployment steps if defined in the general development worklow.
