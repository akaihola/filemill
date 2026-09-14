# Issue tracking for Filemill

Rules for TASKS.md usage are at the bottom of the file.

## Unverified proposals

- [9] Consider bundling VFS preview parameters in `ViewSpec`. This is an unverified
  architecture proposal, conditional on a fourth provider or a pagination bug.

## Scheduled

- [*] Add root `CONTRIBUTING.md` (setup, tests, commit style, STE rule), `SECURITY.md`
  (threat model, how to report) and `CHANGELOG.md` (Keep a Changelog format).

- [16] Rewrite all remaining Markdown files in Simplified Technical English. Done when
  the Markdown line count is below the line count of `*.py`, `*.js` and `*.css`.

- [17] Convert `ui/core/` and `ui/adapters/` to ES modules with one entry module per
  edition. Make `static/build-index.py` inline the module graph.

- [*] Document the full port contract in `ui/core/ports.js`: `FS.node`, `FS.blob`,
  `ROUTER.write(state, replace)`, `RouterPath.base` and every node field.

- [21] Cache the preview element keyed on the previewed node and its `meta`, the same
  way `colCache` keys columns. A resize must cause zero `PREVIEW.render` calls.

- [22] Replace `cursor[i]`, `sel[i]` and `node.lastSel` with one selection model:
  `sel[i]` is the selected name. Derive the row index when needed.

- [*] Split `applyScroll` in `ui/core/layout.js` into `foldFromScroll`, `applyWidths`,
  `panFocus` and `slideTail`. Each function is under 25 lines.

## Ordered backlog

- Feature: Move to using `pptx-vanilla-viewer` from a CDN for previewing PowerPoint
  files. Current PPTX support was implemented in task
  38ab06e2-c607-4d4a-9978-67847e70d27d.

- [x] Delete `_document_page` — document representations, including `layout=no-columns`,
      now return the shared client shell.

- [x] Write `docs/adr/0001-one-finder.md` (context, decision, measurement, consequence).
      The shared UI owns all interaction. The server renders documents. Proposal [8] is
      closed.

- [x] [13] Correct the stale claims that review finding 15 lists in `server/README.md`,
      `server/CONTRIBUTING.md`, `server/TASKS.md`, `docs/tasks/2-*.md` and root
      `TASKS.md`.

- [18] Break the import cycles in `ui/core/`: `render.js` gets its callbacks as one
  `actions` object at boot; `layout.js` gets `set` and `setVar` from a new `dom.js`.
    - Depends on: [17]

- [19] Move adapter code out of `ui/core/`: `jsonl.js`, the welcome screen, the local
  badge and `offerRichToggle` go to `ui/adapters/`.
    - Depends on: [17]

- [20] Create `ui/core/limits.js` with one `TEXT_MAX` and one image extension list.
  Create one `mountRoot()` and one `currentPath()`. Delete the copies and `pathParts`.
    - Depends on: [17]

- [*] In `ui/adapters/vfs-json.js`, merge `withJsonl` and `withJson` into `withVirtual`,
  and `withJsonlPreview` and `withJsonPreview` into `withVirtualPreview`.
    - Depends on: [19]

- [*] Give each magic number in `ui/core/state.js`, `layout.js`, `nav.js`, `render.js` a
  name and a one-line comment that says why the value is what it is.

- [23] Write the narrow-screen layout model as an ADR: what folds, what pans, what stays
  on screen. Add one test each for phone portrait, phone landscape, tablet and desktop.

- [6] Centralize file-kind classification across filesystem producers and preview/edit
  consumers. Add one test table per language that both sides share.
    - Depends on: [19]

- [7] Make entry ordering an adapter-owned contract.
    - Depends on: [6]

- [32] Render Markdown and `.docx` in the browser in the server edition too. Serve the
  pinned renderer modules from `ui/vendor/`. Then delete `rendering.py` and its deps.
    - Depends on: [19]

- [33] Keep the URL contract, drop the server-side representations: the server sends
  bytes for `?filemill=raw` and the shell for all else. The client renders the view.
    - Depends on: [32]

- [34] Make the SQLite provider return JSON only. The client renders tables and rows
  with the JSON hierarchical view. Delete the HTML in `providers/sqlite.py`. Close [9].
    - Depends on: [19]

- [*] Delete `/api/render` in `app.py`, `render_upload` in `api.py` and
  `ui/adapters/preview-upload.js`. Local folders in the server edition use PreviewRich.
    - Depends on: [32], [34]

- [*] Delete `/sse/reload` and `LIVE_MODE` in `app.py`, `LIVE_RELOAD_JS` in `styles.py`
  and the `watchfiles` dependency. Delete their tests.

- [*] Delete `/open-link` and `_parse_desktop_url` in `app.py`. `desktopCard` in
  `ui/adapters/preview-local.js` already handles `.desktop` files in both editions.

- [*] Delete `providers/json_provider.py`, `providers/csv_provider.py` and their
  registration in `vfs.py`. JSON is a browser virtual filesystem. CSV comes in phase 8.

- [*] Delete `server/src/filemill/styles.py`. The shell links `/ui/core/styles.css`, and
  no other server route emits HTML. Delete the tests that pin `APP_CSS`.
    - Depends on: [33], [34]

- [35] Decide the fate of the `/w/` named mounts and their CORS middleware: delete them,
  or make CORS opt-in and document it in `SECURITY.md`.
    - Depends on: [32]

- [*] Delete the `/raw?path=` route in `app.py`. The client builds `${API}/raw?p=` URLs
  for images, PDF and HTML. Done when `grep -r raw?path server/src` prints nothing.
    - Depends on: [33]

- [24] Reduce `app.py` to routing: move `_resolve_safe` and the symlink map to
  `paths.py` and the PWA routes to `pwa.py`. No imports inside functions.
    - Depends on: [33], [34]

- [*] Compute the symlink zone map one time per request in `paths.py`. Delete the three
  other walks of the root that build the same map.
    - Depends on: [24]

- [*] Default `--bind` in `server/src/filemill/cli.py` to `127.0.0.1`. Document it in
  `SECURITY.md`.

- [*] Replace `python-fasthtml` with `starlette` and `uvicorn`. The shell becomes one
  string template. Done when `dependencies` has starlette, uvicorn, typer, python-pptx.
    - Depends on: [24]

- [25] Move `static/test-ui.py`, `test-url.py` and `test-rich.py` under pytest with
  fixtures for the fake handle, the OPFS root and the bundle. Split `main()` by section.

- [*] Replace every `wait_for_timeout` in `static/*.py` and `server/tests/` with
  `wait_for_function` or `expect`. Done when `grep -r wait_for_timeout` finds nothing.

- [*] Run the static and server browser tests through one root `conftest.py` and one
  Playwright fixture. Delete the CDN proxy plumbing in `test_browser_keyboard.py`.
    - Depends on: [25]

- [*] Keep `static/test-e2e.py` as a manual check. Describe when and how to run it in
  `static/FSA-TEST-CHECKLIST.md`.

- [*] Stop `server/tests/conftest.py` from changing the module global `ROOT`. Done when
  `uv run pytest -n auto` passes at the repository root.

- [26] Create one renderer registry, a list of `{kind, render, fallback}`. Both editions
  fill it from the same core list plus their own adapters.
    - Depends on: [19]

- [*] Implement CSV as a browser virtual filesystem in `ui/adapters/vfs-csv.js`, like
  JSONL: one entry per row, a key/value preview per row. No Python. Closes issue #49.
    - Depends on: [26]

- [*] Render `.pptx` in the browser: unzip the file and show the slide text, as one
  registry entry. Then delete `_preview_pptx`, `python-pptx` and `/api/preview`.
    - Depends on: [26]

- [*] Add a preview for `.mp4` files with a `<video controls>` element, as one registry
  entry plus one test.
    - Depends on: [26]

- [27] Try reStructuredText rendering in the browser with Pyodide or a WASM tool, behind
  the rich renderer consent switch. Record size and first-load time in an ADR.
    - Depends on: [26]

- [28] Grow the editor behind the `FS.write` port: undo, find, a line gutter and a
  "modified" mark. Each addition is one file in `ui/editor/`.
    - Depends on: [17]

- [29] Make `ui/core/` a model package with no DOM: nodes, selection, folding
  arithmetic, keyboard map and deep links. Keep a thin DOM renderer beside it.
    - Depends on: [18], [21]

- [30] Prototype one native shell that hosts the DOM renderer in a WebView and supplies
  the three ports natively. Choose the smallest binary that passes `test-ui.py`.
    - Depends on: [29]

- [31] Evaluate AppKit, GTK and WinUI against the WebView prototype. Record the
  comparison in an ADR. Do not start a native toolkit before the ADR exists.
    - Depends on: [30]

- Clarify the meaning of `[~]` in this file. Review Kandev task sessions to find out
  what it means.

- The server browser suites show 11 failures on the branch, but a run against a clean
  main checkout produced exactly the same 11: two legacy-htmx tests that main
  deliberately disabled, and nine mobile restore-scroll tests.

- In keyboard navigation, parent folder columns currently unfold when selecting the next
  item using the down arrow. Strangely, this doesn't happen when using the up arrow. I
  haven't been able to understand what's special about the folders that cause this
  behavior.

- Navigating with the right arrow key to the preview area must fold all folder columns
  to maximize the preview area width. A left arrow should return to the parent folder of
  the reviewed document and unfold that folder column (but no ancestor folder columns).

- Task 04ce9574-92c8-4a4c-8148-32d2e827c13d didn't fix the erratic folding/unfolding of
  the parent column. Hard rule: Up/down navigation must never change folding state of
  ancestor folder columns.

- Keyboard navigation using arrows still doesn't animate folding/unfolding/resizing of
  columns. Do systematic debugging to identify the cause, and fix it.

- [*] Each row of a JSONL file must be presented exactly like a hierarchical nested view
  of a JSON file. Depends on [5].

- For hierarchical nested view of JSON, don't use the folder icon. Use the JSON icon for
  the whole file, and `{}` and `[]` icons for objects and arrays.

- When an object or list is selected in a hierarchical nested view of JSON, show the
  child nodes in the column to the right, and a foldable highlighted and pretty-printed
  JSON preview of the selected item in the second column to the right.

- The `Fullscreen` button in the preview pane doesn't do anything. No errors seen on the
  JavaScript console either.

## Scheduled

- [14] Merge `server/TASKS.md`, `server/ISSUES.md` and `static/TASKS.md` into root
  `TASKS.md` and `docs/tasks/`. Keep open items. Delete closed items and the files.

- [*] Remove every `# noqa: S608` in `server/src/filemill/providers/sqlite.py`. Quote
  identifiers with `"` and replace `"` inside them with `""`, or check `sqlite_master`.

- [*] Bug: Markdown preview doesn't fill and wrap paragraphs at the width of the
  preview, but keeps linefeeds. Consecutive lines of text must be considered as a single
  paragraph. If this can't be changed by configuring the Markdown renderer currently in
  use, consider alternative renderers, check whether they support the other features
  currently supported (e.g. checkboxes and wikilinks). Tradeoffs must be discussed with the
  maintainer before implementing.

- [~] Typing a right arrow when the rightmost column before the preview is focused
  should focus the preview and let the user scroll it up/down using the arrow and
  PgUp/PgDn keys.

- [*] Using the `Search file contents` input always causes the error
  `Search error: Search timed out` to display. JavaScript console:
  `XHR GET https://gogo.crane-boa.ts.net:8445/api/search?q=development [HTTP/2 503  2020ms]`.
  Originally implemented in task 456736f9-7242-40d0-894d-d5e1db50c0de.

- [x] Delete `static/hotreload.py`, `forgetRoots` in `ui/adapters/storage.js`, and
      `PYGMENTS_FORMATTER` and the second `FRIENDLY_CSS` in
      `server/src/filemill/styles.py`.

- Back-navigation still often fails to unfold the newly focused column.

## In progress

- [15] Split the decisions table in `static/AGENTS.md` into one dated ADR file per
  decision in `docs/adr/`. Each file has context, decision, measurement, consequences.

- [*] Delete `server/PLAN-18.md`, `PLAN-19.md`, `PLAN-20-shared-frontend.md` and
  `server/lmt/`. Move a paragraph only if it is still true and is not elsewhere.

- [*] Make root `README.md` the one explanation of the two editions and their ports.
  `server/README.md` and `static/AGENTS.md` link to it and keep edition-specific text.

- [*] Delete `server/.pi/settings.json`, `server/mobile-narrow-preview.png`,
  `server/.claude/commands/` and `architecture-review-20260904.html`.

- Feature: In addition to the `Raw` and `Fullscreen` buttons, there needs to be a toggle
  between viewing the document rendered (e.g. HTML, Markdown, reStructuredText) and
  viewing the source with syntax highlighting.

- [*] Add `.pre-commit-config.yaml` with ruff, ruff-format, mypy, deno fmt, deno lint
  and `static/build-index.py --check`. Run `pre-commit run --all-files` until it passes.

- Bug: Task 511f90cc-2725-4ef1-a8d8-ed67c4eddb0f failed to fix the portrait mobile
  scroll to the right problem. I suspect the extra space at the right side of the page
  is caused by the `⇧+wheel fold` label flowing outside the right edge of the page.

- Feature: ability to delete a file or a directory from the file manager.

- [~] Feature: Syntax highlight Markdown and HTML files in the `?filemill=highlight` view.

- Bug: After navigating from a directory url without query parameters (e.g.
  `/path/to/dir`) to a file (e.g. `file1.md`), and then another file (e.g. `file2.md`),
  and then opening file2 using the `Raw` button, and navigating back using the browser's
  back button, in some situations the file manager view isn't displayed. Instead, the
  raw view of file1 is shown. Navigating to files needs to always include the
  `?filemill=render` or `?filemill=highlight` query parameter (whichever mode was last
  active) to prevent this behavior.

- Bug: For `.vtt` files from YouTube, this error is always displayed instead of the
  content: `Malformed WebVTT: cue is missing a timestamp`. You may test using `.vtt`
  files found on the filesystem.

- [*] In an installed PWA, there is no way to get back from raw file view to the file
  manager view.

- [*] Using the `Search file contents` input always causes the error
  `Search error: Search timed out` to display. JavaScript console:
  `XHR GET https://gogo.crane-boa.ts.net:8445/api/search?q=development [HTTP/2 503  2020ms]`.
  Originally implemented in task 456736f9-7242-40d0-894d-d5e1db50c0de.

- [*] In the CSV hierarchical preview, there are two problems. The first column is
  always selected as the key. Instead, a unique column should be selected similar to how
  it's done in JSON. Also, currently if the first column is not unique, all identical
  values are selected together. This should be fixed for the case when no unique column
  is available. Original implementation in task 8038a32c-570b-45ed-b3ca-5834b3b8dc18.

- [*] `.py.j2` are templates for Python files that are rendered by Jinja2. Does our
  highlighting library support syntax highlighting for such hybrid files? If so,
  implement that. If not, consider alternatives and write a report.

- [*] On portrait mobile, a horizontal left swipe now eventually shows the preview which
  fills the screen. Good. But an additional left swipe on the screen-filling preview
  scrolls the entire page about 1/12th width and leaves an empty margin at the right
  edge.

- [~] Add `deno fmt` and `deno lint` for `ui/` (one pinned binary, no Node project).
  Format `ui/` one time and commit the result as its own commit.

- [*] Add `ruff` and `mypy` to the `dev` group in `server/pyproject.toml`. Add
  `[tool.ruff]` with `line-length = 88`. Fix all findings. Run `ruff format`.

- [x] Add a `LICENSE` file with the MIT license text. `README.md` already says MIT. Use
      the current year and "Antti Kaihola" as the copyright holder.

- [*] In the preview pane top bar, add buttons for viewing the raw file
  (`/path/to/file.ext` without query parameters), toggling highlighted source vs
  rendered preview (for file types in which applicable), and toggling fullscreen mode
  (hide `div#bar` and `div#status` and filling `div#strip` with only the `div#preview`
  without borders and padding).

- [12] Make `static/test-ui.py` run to its end, then fix the three checks that fail: the
  `.pv-content` timeout and the two "edit starts at the top" checks.

- Markdown preview now preserves line breaks. It should instead let the browser handle
  line breaks and consider a multi-line Markdown paragraph as a single line.

- [*] In `ui/core/state.js`, replace `node.jsonl ? kids : sortKids(kids)` with a
  `node.ordered` flag. Each virtual provider (JSON, JSONL, SQLite) sets the flag.

## Completed

- [*] Add a `lint` job to `.github/workflows/publish.yml` that runs
  `pre-commit run --all-files`. Make the `test` job need the `lint` job.

- [x] Remove the `--cov*` options from `addopts` in `server/pyproject.toml`. Pass them
      on the `pytest` command line in the CI `test` job. A single-test run must be fast.

- [*] Rendering if reStructuredText (`.rst`) isn't currently supported. Investigate how
  to implement it on the client side. Prefer readily available 3rd party client-side
  solutions, or pre-packaged Python solutions to run on the browser, and just implement
  whatever best solution you find. If those solutions aren't available, plan a fallback
  solution for how to run the Python code on the browser by ourselves, but write a plan
  first without implementing it yet.

- [x] Use `/path/to/file.html` instead of `/raw?path=/path/to/file.html` for HTML
      previews. Server HTML iframes now use canonical root-relative file paths.

- [8] One shared JavaScript finder owns interaction. The server supplies API data and
  document previews. Decision recorded in `docs/adr/0001-one-finder.md`.

- [11] Delete the HTMX finder from the server: its Python code, its CSS, its JavaScript
  and its tests. Roadmap phase 0, step 1. Done: the `/click`, `/vpage`, `/restore`,
  `/f/` route handlers and `columns.py` were already unregistered dead code; deleted
  them plus `COLUMN_JS`, the HTMX-only `APP_CSS` rules, the sqlite pagination/format
  HTML, and every test that pinned that stack. The `layout=no-columns` directory listing
  (the one live `columns.py` caller) now uses a small non-HTMX helper.

- [*] Rebuild the static bundle: run `cd static && ./build-index.py` and commit
  `static/index.html`. Roadmap phase 0, step 0.

- [~] Text file editing shows the original version of the file after saving changes.
  Force reloading the page doesn't change that.

- [*] Truncate too wide file names in the middle just before the file extension

- [*] Text file editing should start with the cursor at the top of the file

- [5] Hierarchical nested view for JSON

- [~] Back-navigation still often fails to unfold the newly focused column. For example,
  if I navigate using the keyboard to
  https://filemill.vempai.men/filemill/server/src/filemill/providers/__pycache__/__init__.cpython-313.pyc
  and then back left, the `server` column doesn't unfold.

- [*] Make the static/test-rich.py offline checks deterministic

- [5] Hierarchical nested view for JSON — shared client-side hierarchical JSON view with
  nested navigation and scalar previews.

- [*] Get rid of HTMX based routes. We now have enough feature parity in the stand-alone
  client side UI and the server-based implementation which shares the same client side
  implementation so we can start removing the legacy implementation.

- [*] Allow editing any plaintext file, e.g. `.gitconfig`. Detect editable files by file
  extension **and** contents. If it's plain ASCII or UTF-8 text, it's editable, unless
  it's single line and insanely wide.

- [*] For highlighted text files (e.g. `.py`, `.js`), the minimum preview width isn't
  currently defined as a static number of characters. So at browser zooms above 100%,
  lines are wrapped. Ensure the minimum preview width is 88 characters.

- [*] If I navigate deep into `~/.bun/install/cache/@agegr/pi-web/0.8.8@@@1/README.md`
  and return back column by column using the left arrow key, the `.bun` column doesn't
  expand when I reach it. It does expand if I navigate to it using the mouse instead.

- [*] make PDF previews full frame just like HTML and Markdown rendered previews

- [*] The maximum column width must be 2/3 of available space. This ensures that the
  left edge of inner folders and previewed files is always visible.

- [*] Rendering of fenced blocks in Markdown has two unwanted artifacts:
    - the first line is indented about 0.7 character widths
    - text has a slightly darker background color than the gray surrounding box

- [*] JSONL hierarchical view must be in original file order, not sorted by key.

- [*] Page Up and Page Down keys should move the selection to the topmost/bottommost
  visible item in the focused column, or if already selected, scroll up/down as many
  lines as fit in the column, and then move to the topmost/bottommost visible item.

- [4] Use one shared client side implementation for rendering Markdown fenced code
  blocks. Make sure the implementation flows line-wrapped paragraphs correctly, i.e.
  doesn't insert line feeds in the rendered HTML at each newline in the source.

- [*] Hierarchical view for `.jsonl` files: first level column is a listing showing for
  each line the value of a key which is unique across all lines, preferring short or
  moderate width text values (e.g. `title`, `description`) but using scalar values (e.g.
  `timestamp`, `id`) if none are available. The second column is a two-column table view
  of `(key, value)` pairs for each line. Do this entirely on the client side, but
  following the example of how `.sqlite` files are rendered.

- [*] Migrate the 19 legacy htmx browser tests in server/tests/test_browser_keyboard.py
  to the shared UI. Ported in e89f974; the file's 31 tests all pass. Details in
  docs/tasks/2-fix-all-test-failures.md.

- [3] Get rid of duplicate vendored code. Simply use the same source files for ui/ and
  server/.

- [*] Full file highlighting: don't clip at 8000 chars. Answered: no slicing — a text
  preview is whole or absent, bounded by the 512 KB read gate that was always there.
  Rationale in static/AGENTS.md.

- [*] On mobile, tapping a folder still hid the tapped row when the column held wide
  content. The fold cap kept that column unfolded but not on screen: each folded
  ancestor costs a spine and a gutter, so at 390 px two levels in left 292 px of a 376
  px column inside the viewport. applyScroll now pans the strip left by exactly the
  overflow, and render clamps a column to the stage width.

- [*] On mobile, opening a folder causes the opened folder in the next column to fold
  (when vertical) or the parent folder to fold (when horizontal). Touching folders
  should never cause folding of the touched column or columns to the right. Only columns
  to the left of the touched column may fold.

- [*] The static/test-ui.py check "Scrolling right folds columns into spines" (expects 5
  spines) fails or flakes, likely an animation-timing race.

- [2] Fix all test failures. Split into multiple tasks if necessary.

- [1] Show version and Git commit hash (if available) via an option in the settings
  menu.

- [*] Plaintext preview doesn't use all vertical space in preview column. The whole
  column should scroll, not just the preview area.

- [*] Syntax highlighting missing in preview pane. Use client side highlighting to
  maximize shared code between ui/ and server/.

- [*] Edit mode for text files in the preview pane

- [*] Remove `dl.meta` section (Where/Size/Modified) from preview pane

- [*] In the cogwheel menu, there's an empty `PREVIEWS` section

- [*] Verify and refine TASKS.md rules

[1]: docs/tasks/1-show-version-and-git.md
[2]: docs/tasks/2-fix-all-test-failures.md
[3]: docs/tasks/3-remove-duplicate-ui-source.md
[4]: docs/tasks/4-share-markdown-code.md
[5]: docs/tasks/5-hierarchical-json-view.md
[6]: docs/tasks/6-file-kind-classification.md
[7]: docs/tasks/7-adapter-owned-entry-order.md
[8]: docs/tasks/8-consolidate-finder-stacks.md
[9]: docs/tasks/9-vfs-viewspec.md
[11]: docs/tasks/11-delete-htmx-finder.md
[12]: docs/tasks/12-test-ui-runs-to-end.md
[13]: docs/tasks/13-correct-stale-documents.md
[14]: docs/tasks/14-merge-issue-trackers.md
[15]: docs/tasks/15-split-decisions-into-adrs.md
[16]: docs/tasks/16-rewrite-docs-in-ste.md
[17]: docs/tasks/17-es-modules.md
[18]: docs/tasks/18-break-import-cycles.md
[19]: docs/tasks/19-adapter-code-out-of-core.md
[20]: docs/tasks/20-one-limits-one-path.md
[21]: docs/tasks/21-cache-preview-element.md
[22]: docs/tasks/22-one-selection-model.md
[23]: docs/tasks/23-narrow-screen-model.md
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
[*]: TASKS.md

---

## Rules

Here are the rules for TASKS.md usage:

### TASKS.md maintenance sessions

- Each backlog item must be prefixed with either
    - a numbered reference-style link (e.g. `[1]`) to a description file, or
    - `[*]` to indicate no description file is needed for a simple task.
- Link references are listed between `## Completed` and `## Rules`.
- If any issue is missing a link:
    - Create the first missing numbered description file in
      docs/tasks/<N-issue-description>.md and add the link

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

- Move the issue under `## In progress` in `TASKS.md` in the worktree branch, ensure
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
- Move the issue from `## In progress` to `## Completed` in TASKS.md and commit.
- Do any deployment steps if defined in the general development worklow.
