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

- [*] Bug: PPTX preview only shows the text found on the slides, and omits spaces and
  linefeeds between blocks of text. The preview looks identical in both `Source` and
  `Rendered` views. Task c6f1a55d-3d5d-4259-823f-34ad83f18ef3 failed to implement proper
  PPTX preview. This issue is probably complicated, so let's get help from a strong
  language model and deep online research.

- [*] Bug: Back and Forward navigation doesn't work correctly. Fix browser history
  management so that navigating back and forward works as expected when moving between
  folders and files and raw files. Also make sure `Alt`+`ArrowLeft`/`ArrowRight` works
  as expected.

- [*] Bug: Task bf3498e4-4824-4c34-b7f4-25f7efe8fef7 fixed the `ArrowLeft` navigation
  out from the preview pane incorrectly. Focus now moves to the parent folder of the
  containing folder of the previewed file. Instead, the containing folder column should
  be focused with the previewed file highlighted.

- [*] Bug: Task c37c152d-177e-44f1-a643-9ab96d37b75a failed to implement
  reStructuredText rendering. In the preview pane, `.rst` files appear as identical
  plain unhighlighted text both in `Source` (`?filemill=highlight`) and `Rendered`
  (`filemill=render`) modes. Use red-green TDD and a strong model to investigate and fix
  this.

- [*] Bug: `[](~/...)` links are rendered incorrectly. For example, the path in
  `[pykoclaw-acp/backlog/004](~/prg/pykoclaw-dev/pykoclaw-acp/backlog/004-tool-call-visibility.md#streaming-restore-plan-buffered-semantic-windows)`
  is turned into the href
  `/w/agent/prg/pykoclaw-dev/pykoclaw-acp/backlog/004-tool-call-visibility.md#streaming-restore-plan-buffered-semantic-windows`
  when rendered. It should omit the `/w/agent/` prefix. Task
  301fd540-e206-4306-b88f-5b3dbe1a15ec attempted but failed in making this link
  expansion correct.

- [*] Feature: Clicking on a content search result now opens the raw file. Open the
  rendered file in the UI preview pane instead.

## Scheduled

- [*] Treat `.py.j2` as Python.

## In Progress

- [*] Delete `providers/json_provider.py`, `providers/csv_provider.py` and their
  registration in `vfs.py`. JSON is a browser virtual filesystem. CSV comes in phase 8.

- [*] Default `--bind` in `server/src/filemill/cli.py` to `127.0.0.1`. Document it in
  `SECURITY.md`.

- [*] Replace every `wait_for_timeout` in `static/*.py` and `server/tests/` with
  `wait_for_function` or `expect`. Done when `grep -r wait_for_timeout` finds nothing.

- [*] The server browser suites show 11 failures on the branch, but a run against a clean
  main checkout produced exactly the same 11: two legacy-htmx tests that main
  deliberately disabled, and nine mobile restore-scroll tests.

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

- [*] For user testing, document how to run on agent@gogo instances of Filemill that are
  as close as possible to the browser test setup you have in the test suite. Put each
  different browser test setup in its own HTTP port, and link them in
  `/home/agent/index.html`. We will separately set up systemd user services for each
  different browser test setup.

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
  JSONL: one entry per row, a key/value preview per row. No Python. Closes issue #49.
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

- [*] When an object or list is selected in a hierarchical nested view of JSON, show the
  child nodes in the column to the right, and a foldable highlighted and pretty-printed
  JSON preview of the selected item in the second column to the right.

- [*] In keyboard navigation, parent folder columns currently unfold when selecting the next
  item using the down arrow. Strangely, this doesn't happen when using the up arrow. I
  haven't been able to understand what's special about the folders that cause this
  behavior.

- [*] Keyboard navigation using arrows still doesn't animate folding/unfolding/resizing of
  columns. Do systematic debugging to identify the cause, and fix it.

- [7] Make entry ordering an adapter-owned contract.
    - Depends on: [6]

- [*] Navigating with the right arrow key to the preview area must fold all folder columns
  to maximize the preview area width. A left arrow should return to the parent folder of
  the reviewed document and unfold that folder column (but no ancestor folder columns).

- [*] Task 04ce9574-92c8-4a4c-8148-32d2e827c13d didn't fix the erratic folding/unfolding of
  the parent column. Hard rule: Up/down navigation must never change folding state of
  ancestor folder columns.

- [*] Add a PWA manifest and service worker to the static bundle so `static/index.html`
  installs as a standalone window. The server edition already serves `/manifest.json`.

- [*] Task e02c3b0b-21a0-4be0-bcdd-bce0d99206f4 didn't fix file content search. It
  either returns `Search error: search result too large` or `No matches`. Make sure
  search only covers the current focused directory and its subdirectories recursively.
  Do red-green testing: first reproduce, then investigate, plan, implement, and test.
  Iterate until fixed.

- [*] The `Fullscreen` button in the preview pane doesn't do anything. No errors seen on the
  JavaScript console either.

- [*] `.rst` files still don't render or highlight at all even though task
  63b87ad4-33c9-4f45-ae24-280034e8b0eb claims to have implemented and tested it. Do
  red-green testing, investigate, and fix.

- [*] Opening `https://gogo.crane-boa.ts.net:8445/<any path>` without query parameters
  redirects to `https://gogo.crane-boa.ts.net:8445/` and spins `Reading...` for a very
  long time (if not forever). It should instead return files raw with the correct
  content type.

- [*] Bug: after focusing the preview pane using the arrow right key, the arrow left key
  doesn't return back and focus the parent column. Instead, it scrolls the page
  horizontally to the left. Make sure the arrow left key returns to the parent column
  after focusing the preview pane.

- [*] Remove every `# noqa: S608` in `server/src/filemill/providers/sqlite.py`. Quote
  identifiers with `"` and replace `"` inside them with `""`, or check `sqlite_master`.

- [*] Bug: Markdown preview doesn't fill and wrap paragraphs at the width of the
  preview, but keeps linefeeds. Consecutive lines of text must be considered as a single
  paragraph. If this can't be changed by configuring the Markdown renderer currently in
  use, consider alternative renderers, check whether they support the other features
  currently supported (e.g. checkboxes and wikilinks). Tradeoffs must be discussed with
  the maintainer before implementing.

- [*] Typing a right arrow when the rightmost column before the preview is focused
  should focus the preview and let the user scroll it up/down using the arrow and
  PgUp/PgDn keys.

- [*] Delete `static/hotreload.py`, `forgetRoots` in `ui/adapters/storage.js`, and
      `PYGMENTS_FORMATTER` and the second `FRIENDLY_CSS` in
      `server/src/filemill/styles.py`.

- [*] On portrait mobile, some `.md` files wrap at screen width, others run wider than
  the screen width. For example, in the filemill repository, `README.md` and
  `CHANGELOG.md`, `SECURITY.md`, and `TASKS.md` wrap at screen width, but
  `CONTRIBUTING.md` runs wider. All `.md` files should wrap at screen width on portrait
  mobile.

- [*] GET https://gogo.crane-boa.ts.net:8445/favicon.ico

    ```
    [HTTP/2 404  6ms]
    Uncaught (in promise) TypeError: renderPage is not a function
        applyPath https://gogo.crane-boa.ts.net:8445/ui/core/deeplink.js:123
        mountServer https://gogo.crane-boa.ts.net:8445/ui/adapters/app-http.js:117
        async* https://gogo.crane-boa.ts.net:8445/ui/adapters/app-http.js:201
    deeplink.js:123:5
    ```

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

- [*] Feature: In addition to the `Raw` and `Fullscreen` buttons, there needs to be a toggle
  between viewing the document rendered (e.g. HTML, Markdown, reStructuredText) and
  viewing the source with syntax highlighting.

- [*] Add `.pre-commit-config.yaml` with ruff, ruff-format, mypy, deno fmt, deno lint
  and `static/build-index.py --check`. Run `pre-commit run --all-files` until it passes.

- [*] Bug: Task 511f90cc-2725-4ef1-a8d8-ed67c4eddb0f failed to fix the portrait mobile
  scroll to the right problem. I suspect the extra space at the right side of the page
  is caused by the `⇧+wheel fold` label flowing outside the right edge of the page.

- [*] Feature: ability to delete a file or a directory from the file manager.

- [*] Feature: Syntax highlight Markdown and HTML files in the `?filemill=highlight`
  view.

- [*] Bug: After navigating from a directory url without query parameters (e.g.
  `/path/to/dir`) to a file (e.g. `file1.md`), and then another file (e.g. `file2.md`),
  and then opening file2 using the `Raw` button, and navigating back using the browser's
  back button, in some situations the file manager view isn't displayed. Instead, the
  raw view of file1 is shown. Navigating to files needs to always include the
  `?filemill=render` or `?filemill=highlight` query parameter (whichever mode was last
  active) to prevent this behavior.

- [*] Bug: For `.vtt` files from YouTube, this error is always displayed instead of the
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

- [37] `.py.j2` are templates for Python files that are rendered by Jinja2. Does our
  highlighting library support syntax highlighting for such hybrid files? If so,
  implement that. If not, consider alternatives and write a report.

- [*] On portrait mobile, a horizontal left swipe now eventually shows the preview which
  fills the screen. Good. But an additional left swipe on the screen-filling preview
  scrolls the entire page about 1/12th width and leaves an empty margin at the right
  edge.

- [*] Add `deno fmt` and `deno lint` for `ui/` (one pinned binary, no Node project).
  Format `ui/` one time and commit the result as its own commit.

- [*] Add `ruff` and `mypy` to the `dev` group in `server/pyproject.toml`. Add
  `[tool.ruff]` with `line-length = 88`. Fix all findings. Run `ruff format`.

- [*] In the preview pane top bar, add buttons for viewing the raw file
  (`/path/to/file.ext` without query parameters), toggling highlighted source vs
  rendered preview (for file types in which applicable), and toggling fullscreen mode
  (hide `div#bar` and `div#status` and filling `div#strip` with only the `div#preview`
  without borders and padding).

- [12] Make `static/test-ui.py` run to its end, then fix the three checks that fail: the
  `.pv-content` timeout and the two "edit starts at the top" checks.

- [*] Markdown preview now preserves line breaks. It should instead let the browser handle
  line breaks and consider a multi-line Markdown paragraph as a single line.

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

- [9] Consider bundling VFS preview parameters in `ViewSpec`. This is an unverified
  architecture proposal, conditional on a fourth provider or a pagination bug.

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
[37]: docs/tasks/py-j2-highlighting.md
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
