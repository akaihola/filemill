# Issue tracking for Filemill

Rules for TASKS.md usage are at the bottom of the file.

## Unverified proposals

- [*] From documentation, docstrings and comments, remove references to specific
  development setups which include e.g. server names and local paths.

## Ordered backlog

- [86] Markdown in archives is not rendered

- [82] Update stale Playwright 1.61 pins and the server renderer note in docs

- [81] Horizontal scrolling fold "stops"
  <!-- hai:{"id":"simple-d01a5118-704f-4133-953c-ead294dbc119","priority":"none","labels":[],"createdAt":"2026-10-08T19:19:18.607Z","updatedAt":"2026-10-08T19:19:18.607Z"} -->

- [80] Left arrow doesn't preview the whole document after returning from per-section preview
  <!-- hai:{"id":"simple-c4d74fd6-cd42-426e-9cda-819fbf9965c3","priority":"none","labels":[],"createdAt":"2026-10-08T16:24:33.129Z","updatedAt":"2026-10-08T16:24:33.129Z"} -->

- [79] Remove § signs and redundant headings from document section previews
  <!-- hai:{"id":"simple-e6ef425c-e474-4559-b792-1e21478c71bb","priority":"none","labels":[],"createdAt":"2026-10-08T16:21:55.597Z","updatedAt":"2026-10-08T16:21:55.597Z"} -->

- [78] Wide document scrolls instead of expanding the preview
  <!-- hai:{"id":"simple-78e15d9a-0d90-4186-953f-46fdddf6fe5c","priority":"none","labels":[],"createdAt":"2026-10-08T16:19:43.075Z","updatedAt":"2026-10-08T16:19:43.075Z"} -->

## Scheduled

- [85] Images in archives are not scaled to the preview pane
  <!-- hai:{"updatedAt":"2026-10-10T22:15:23.061Z"} -->

## In Progress

- [87] Make CI green so GitHub Pages publishes
  <!-- hai:{"updatedAt":"2026-10-10T19:58:38.726Z"} -->

- [*] `.jsonl` files larger than 512 KB aren't previewed or made navigable in a contents
  column. Instead, the message `⚠ Too large to browse (over 512 KB)` appears in the
  column. Solve handling of large `.jsonl` files. Use Fable Medium to solve this. Use
  3rd party libraries if that helps.

- [*] When all folder columns are collapsed, exiting the preview pane using the arrow
  left key doesn't currently expand the parent folder column (rightmost folder column
  just before the preview pane). Make sure left arrow always expands the parent folder
  column.

- [*] Treat `.py.j2` as Python.

- [*] When returning focus back to the containing folder from the preview pane using the
  left arrow key, always keep all ancestor folder columns in the same expanded/collapsed
  state as they are. Currently expanded ancestor folders are collapsed if I hit the left
  arrow key.

- [*] Add the `Delete` key as a shortcut to delete the current file or directory.

- [30] Prototype one native shell that hosts the DOM renderer in a WebView and supplies
  the three ports natively. Choose the smallest binary that passes `test-ui.py`.
    - Depends on: [29]

- [64] Keep subfolder and folded parent widths stable during Up/Down navigation.

- [41] Fix plain-text reStructuredText previews in Source and Rendered modes.

- [*] Delete `providers/json_provider.py`, `providers/csv_provider.py` and their
  registration in `vfs.py`. JSON is a browser virtual filesystem. CSV comes in phase 8.

- [*] Default `--bind` in `server/src/filemill/cli.py` to `127.0.0.1`. Document it in
  `SECURITY.md`.

- [*] Replace every `wait_for_timeout` in `static/*.py` and `server/tests/` with
  `wait_for_function` or `expect`. Done when `grep -r wait_for_timeout` finds nothing.

- [43] Investigate the 11 server browser failures also reproduced on main.

- [*] Clarify the meaning of `[~]` in this file. Review Kandev task sessions to find out
  what it means.

- [~] Keep `static/test-e2e.py` as a manual check. Describe when and how to run it in
  `static/FSA-TEST-CHECKLIST.md`.

- [25] Move `static/test-ui.py`, `test-url.py` and `test-rich.py` under pytest with
  fixtures for the fake handle, the OPFS root and the bundle. Split `main()` by section.
    - Depends on: [12]

- [*] `.py` files are not highlighted at all.

## Completed / Accepted

- [ ] [84] JSON member in an archive shows a chevron but does not open
  <!-- hai:{"updatedAt":"2026-10-10T22:15:01.018Z"} -->

- [ ] [89] Markdown previews show two Raw buttons
  <!-- hai:{"updatedAt":"2026-10-10T21:58:09.204Z"} -->

- [ ] [88] Status bar hints wrap and get clipped
  <!-- hai:{"updatedAt":"2026-10-10T21:28:47.986Z"} -->

- [ ] [83] Screen-reader search label shows on screen
  <!-- hai:{"updatedAt":"2026-10-10T20:53:33.766Z"} -->

- [ ] [*] Make Git `.bundle` files navigable hierarchically, and if they contain previewable
  files, show them in the preview pane when navigated to.
  <!-- hai:{"id":"simple-ca7153b94516ed5f","updatedAt":"2026-10-10T19:56:48.893Z"} -->

- [ ] Make `.tar.zst` (and other compressed archive) files navigable hierarchically, and
  if they contain previewable files, show them in the preview pane when navigated to.
  <!-- hai:{"id":"simple-8f807623b9f707fd","updatedAt":"2026-10-07T17:13:55.825Z"} -->

- [ ] [*] A 528 kB JSON file like
  https://gogo.crane-boa.ts.net:8445/backups/kasvimuseo-deployment/20261007-010643/backup-manifest.json?f=
  isn't previewed nor navigable hierarchically.
  <!-- hai:{"id":"simple-fec4c3e94daf7040","updatedAt":"2026-10-07T17:25:48.108Z"} -->

- [ ] [*] Similar to JSON and SQLite files, allow hierarchical navigation of Markdown
      and reStructuredText documents based on their headings.
      <!-- hai:{"id":"simple-f8626c1613849773","updatedAt":"2026-10-07T15:40:08.724Z"} -->

- [x] [77] .md tight bullet list line spacing
      <!-- hai:{"id":"simple-f6220ff8-98cd-48a2-b2ab-4744392be4a7","priority":"none","labels":[],"createdAt":"2026-10-06T18:33:12.894Z","updatedAt":"2026-10-07T15:05:44.592Z"} -->

- [x] [39] Fix Back/Forward navigation across folders, previews and raw files.
      <!-- hai:{"updatedAt":"2026-10-07T15:04:51.317Z"} -->
- [x] [*] On iPad, two touches on a folder name are required to open its contents in the
      next column. Only one touch should do it.
      <!-- hai:{"id":"simple-63ca4fc48e67d49a","updatedAt":"2026-10-07T15:03:32.602Z"} -->

- [ ] [65] [*] Bug: PNG and JPEG preview doesn't work reliably. Sometimes the text
      `No inline preview for this file type.` is displayed instead of the image.

- [ ] [*] For hierarchical nested view of JSON, don't use the folder icon. Use the JSON
      icon for the whole file, and `{}` and `[]` icons for objects and arrays.

- [ ] [67] Use the vertical scrollbar to browse large directories instead of pagination.
      Virtualize directory contents efficiently.

- [ ] [*] Per recommendation from task dd6897a9-b54e-4ad4-b9b5-b2372292f4b1, remove
      ?no-columns, wants_columns, and url_for_state. Keep documentation up-to-date.

- [ ] [68] Fix server test fixture discovery from the repository root and document the
      working pytest command.

- [ ] [*] Do issues [38], [39], [40] and [42] each currently sit under both Scheduled
      and In Progress in the tracker? Should they be deduplicated and corrected to sit
      in the correct section so they reflect the implementation?

- [ ] [*] Fix the extra mount prefix in rendered `~/...` Markdown links.
    - Depends on: [42]

- [ ] [*] Check the two architecture reviews (`docs/2026-09-05-ARCHITECTURE-REVIEW.md`
      and `docs/2026-09-19-architecture-review-and-remediation-plan.md`). Remove
      everything that isn't valid any more. De-duplicate and refine. Write into a new
      file and remove the old ones. Use GPT-6-Astra Medium.

- [ ] [*] Implement highlighting of reStructuredText (not actually properly implemented
      by [50]). Ensure unintended highlighting doesn't happen between aposthrophes in
      words. Ensure special roles are highlighted similar to how Pygments does.

- [ ] [42] Render `~/...` Markdown links relative to the root mount, with `?f`, instead
      of deprecated `/w/...` paths.

- [ ] [37] Make the installed PWA show its server-not-running recovery page when opened
      while the server is stopped.

- [ ] [69] Show copied paths in the status bar. Repeat `Ctrl+C` within 5 seconds, with
      no intervening interaction, to cycle relative path, full path and item name.

- [ ] [70] In preview focus, ArrowRight folds the leftmost expanded folder column, then
      enters fullscreen once columns are hidden. ArrowLeft exits fullscreen.

- [ ] [31] Evaluate AppKit, GTK and WinUI against the WebView prototype. Record the
      comparison in an ADR. Do not start a native toolkit before the ADR exists.
    - Depends on: [30]

- [ ] [71] Let reStructuredText paragraphs fill the available preview width, as Markdown
      paragraphs do.

- [ ] [*] The `Delete` button in the preview pane gives the red error
      `Delete failed: actions.render is not a function` on the bottom status line (after
      confirming deletion).

- [ ] [72] Make the browser Back button exit mobile fullscreen preview like Exit
      fullscreen, without leaving an empty preview.

- [ ] [*] There's no way to access the file context menu on desktop browsers. On touch
      devices, a long touch does show it. Also, the context menu is transparent and very
      hard to read. And the `Delete` item is missing from the menu.

- [ ] [*] On a portrait mobile phone, Markdown preview is wider than the screen.
      Contents overflow horizontally both at the left and right edges.

- [ ] [*] Fix all remaining red tests (listed in project memory), including the one-line
      cause of the newest root-column regression.

- [ ] [73] Fix Markdown source highlighting for headings, URLs and links without
      treating word apostrophes as delimiters. Make links clickable.

- [ ] [74] Remember collapsed JSON paths and apply the same collapse pattern to similar
      objects at the same depth.

- [ ] [*] In hierarchical navigation of `.json`, `.jsonl`, and SQLite `.db` files, when
      the key of a scalar value is highlighted, show its value in the preview pane
      instead of rendering the parent JSON structure. If the value is a string and has
      `\n` characters, display it with line breaks.

- [ ] [*] Bug: The `Fullscreen` button causes a full screen view of the file to briefly
      flash, and then immediately returns to the main Filemill UI.

- [ ] [*] When navigating to the parent directory using the left arrow key, make sure
      the highlighted file or directory is scrolled into view.

- [ ] [75] Use stable folder widths in em units and let previews fill the remaining
      space. Tune automatic folding and column/preview ratios for desktop and
      portrait/landscape phones.

- [ ] [*] Bug: Arrow Right into the preview pane works inconasistently. Sometimes it
      focuses the preview pane without changing the layout. Sometimes it hides the
      folder columns and stretches the preview pane to full width.

- [ ] [76] Keep the focused folder column's width stable during Up/Down navigation,
      without partial folding, dimmed text or overlaid folder names.

- [ ] [*] Feature: Clicking on a content search result now opens the raw file. Open the
      rendered file in the UI preview pane instead.

- [ ] [29] Make `ui/core/` a model package with no DOM: nodes, selection, folding
      arithmetic, keyboard map and deep links. Keep a thin DOM renderer beside it.
    - Depends on: [21]

- [ ] [*] Delete `_document_page` — document representations, including
      `layout=no-columns`, now return the shared client shell.

- [ ] [13] Correct the stale claims that review finding 15 lists in `server/README.md`,
      `server/CONTRIBUTING.md`, `server/TASKS.md`, `docs/tasks/2-*.md` and root
      `TASKS.md`.

- [ ] [*] Split `applyScroll` in `ui/core/layout.js` into `foldFromScroll`,
      `applyWidths`, `panFocus` and `slideTail`. Each function is under 25 lines.

- [ ] [15] Split the decisions table in `static/AGENTS.md` into one dated ADR file per
      decision in `docs/adr/`. Each file has context, decision, measurement,
      consequences.

- [ ] [10] Toggling `Source` / `Rendered` reloads the whole page and causes an
      uncomfortable blink and a delay. Just the preview pane should be reloaded, and the
      URL and history updated.

- [ ] [*] Delete the `/raw?path=` route in `app.py`. The client builds `${API}/raw?p=`
      URLs for images, PDF and HTML. Done when `grep -r raw?path server/src` prints
      nothing.
    - Depends on: [33]

- [ ] [*] Virtualise column rows. `content-visibility` made layout cheap, but a 100
      k-entry directory still builds 100 k DOM nodes. Do this only if such folders show
      up.

- [ ] [6] Centralize file-kind classification across filesystem producers and
      preview/edit consumers. Add one test table per language that both sides share.

- [ ] [44] Document demo instances matching each browser test setup.

- [ ] [*] Delete `/open-link` and `_parse_desktop_url` in `app.py`. `desktopCard` in
      `ui/adapters/preview-local.js` already handles `.desktop` files in both editions.

- [ ] [*] Give each magic number in `ui/core/state.js`, `layout.js`, `nav.js`,
      `render.js` a name and a one-line comment that says why the value is what it is.

- [ ] [21] Cache the preview element keyed on the previewed node and its `meta`, the
      same way `colCache` keys columns. A resize must cause zero `PREVIEW.render` calls.

- [ ] [*] Delete `/sse/reload` and `LIVE_MODE` in `app.py`, `LIVE_RELOAD_JS` in
      `styles.py` and the `watchfiles` dependency. Delete their tests.

- [ ] [*] Run the static and server browser tests through one root `conftest.py` and one
      Playwright fixture. Delete the CDN proxy plumbing in `test_browser_keyboard.py`.
    - Depends on: [25]

- [ ] [*] Add a preview for `.mp4` files with a `<video controls>` element, as one
      registry entry plus one test.
    - Depends on: [26]

- [ ] [*] Implement CSV as a browser virtual filesystem in `ui/adapters/vfs-csv.js`,
      like JSONL: one entry per row, a key/value preview per row. No Python. Closes
      legacy server issue #49.
    - Depends on: [26]

- [ ] [*] Compute the symlink zone map one time per request in `paths.py`. Delete the
      three other walks of the root that build the same map.
    - Depends on: [24]

- [ ] [*] Stop `server/tests/conftest.py` from changing the module global `ROOT`. Done
      when `uv run pytest -n auto` passes at the repository root.

- [ ] [*] Replace `python-fasthtml` with `starlette` and `uvicorn`. The shell becomes
      one string template. Done when `dependencies` has starlette, uvicorn, typer,
      python-pptx.
    - Depends on: [24]

- [ ] [*] On mobile, long-pressing a file or directory should open a menu of actions to
      copy its base name, relative path or absolute path.

- [ ] [*] Delete `server/src/filemill/styles.py`. The shell links `/ui/core/styles.css`,
      and no other server route emits HTML. Delete the tests that pin `APP_CSS`.
    - Depends on: [33], [34]

- [ ] [*] Delete `/api/render` in `app.py`, `render_upload` in `api.py` and
      `ui/adapters/preview-upload.js`. Local folders in the server edition use
      PreviewRich.
    - Depends on: [32], [34]

- [ ] [*] Each row of a JSONL file must be presented exactly like a hierarchical nested
      view of a JSON file.

- [ ] [45] Show JSON children beside a foldable preview of the selected value.

- [ ] [46] Fix ancestor columns unfolding during down-arrow navigation.

- [ ] [*] Keyboard navigation using arrows still doesn't animate
      folding/unfolding/resizing of columns. Do systematic debugging to identify the
      cause, and fix it.

- [ ] [7] Make entry ordering an adapter-owned contract.
    - Depends on: [6]

- [ ] [47] Fold folder columns on preview entry and restore the containing column on
      exit.

- [ ] [48] Keep ancestor folding unchanged during Up/Down navigation.

- [ ] [*] Add a PWA manifest and service worker to the static bundle so
      `static/index.html` installs as a standalone window. The server edition already
      serves `/manifest.json`.

- [ ] [49] Fix content search errors and restrict search to the focused directory tree.

- [ ] [*] The `Fullscreen` button in the preview pane doesn't do anything. No errors
      seen on the JavaScript console either.

- [ ] [50] Fix missing reStructuredText rendering and highlighting after the initial
      implementation.

- [ ] [51] Return raw file bytes for URLs without query parameters.

- [ ] [52] Return focus to the parent column when leaving the preview with ArrowLeft.

- [ ] [*] Remove every `# noqa: S608` in `server/src/filemill/providers/sqlite.py`.
      Quote identifiers with `"` and replace `"` inside them with `""`, or check
      `sqlite_master`.

- [ ] [53] Let Markdown paragraphs wrap to the preview width instead of preserving
      linefeeds.

- [ ] [*] Typing a right arrow when the rightmost column before the preview is focused
      should focus the preview and let the user scroll it up/down using the arrow and
      PgUp/PgDn keys.

- [ ] [*] Delete `static/hotreload.py`, `forgetRoots` in `ui/adapters/storage.js`, and
      `PYGMENTS_FORMATTER` and the second `FRIENDLY_CSS` in
      `server/src/filemill/styles.py`.

- [ ] [54] Keep all Markdown previews within the portrait screen width.

- [ ] [55] Fix the favicon 404 and `renderPage is not a function` error.

- [ ] [*] In `ui/adapters/vfs-json.js`, merge `withJsonl` and `withJson` into
      `withVirtual`, and `withJsonlPreview` and `withJsonPreview` into
      `withVirtualPreview`.

- [ ] [20] Create `ui/core/limits.js` with one `TEXT_MAX` and one image extension list.
      Create one `mountRoot()` and one `currentPath()`. Delete the copies and
      `pathParts`.

- [ ] [22] Replace `cursor[i]`, `sel[i]` and `node.lastSel` with one selection model:
      `sel[i]` is the selected name. Derive the row index when needed.

- [ ] [*] Add root `CONTRIBUTING.md` (setup, tests, commit style, STE rule),
      `SECURITY.md` (threat model, how to report) and `CHANGELOG.md` (Keep a Changelog
      format).

- [ ] [*] Document the full port contract in `ui/core/ports.js`: `FS.node`, `FS.blob`,
      `ROUTER.write(state, replace)`, `RouterPath.base` and every node field.

- [ ] [*] Delete `server/PLAN-18.md`, `PLAN-19.md`, `PLAN-20-shared-frontend.md` and
      `server/lmt/`. Move a paragraph only if it is still true and is not elsewhere.

- [ ] [*] Make root `README.md` the one explanation of the two editions and their ports.
      `server/README.md` and `static/AGENTS.md` link to it and keep edition-specific
      text.

- [ ] [*] Delete `server/.pi/settings.json`, `server/mobile-narrow-preview.png`,
      `server/.claude/commands/` and `architecture-review-20260904.html`.

- [ ] [56] Add a Rendered / highlighted Source toggle beside Raw and Fullscreen.

- [ ] [*] Add `.pre-commit-config.yaml` with ruff, ruff-format, mypy, deno fmt, deno
      lint and `static/build-index.py --check`. Run `pre-commit run --all-files` until
      it passes.

- [ ] [57] Fix portrait horizontal overflow potentially caused by the fold hint.

- [ ] [*] Feature: ability to delete a file or a directory from the file manager.

- [ ] [*] Feature: Syntax highlight Markdown and HTML files in the `?filemill=highlight`
      view.

- [ ] [58] Preserve preview mode in file URLs so Back from Raw restores the finder.

- [ ] [59] Fix the missing-timestamp error for YouTube WebVTT files.

- [ ] [*] In an installed PWA, there is no way to get back from raw file view to the
      file manager view.

- [ ] [60] Fix content searches failing with `Search timed out`.

- [ ] [61] Choose unique CSV row keys and keep duplicate values independently
      selectable.

- [ ] [66] Evaluate hybrid Python/Jinja highlighting and report supported alternatives.

- [ ] [62] Prevent further left swipes from exposing a margin beside a fullscreen
      portrait preview.

- [ ] [*] Add `deno fmt` and `deno lint` for `ui/` (one pinned binary, no Node project).
      Format `ui/` one time and commit the result as its own commit.

- [ ] [*] Add `ruff` and `mypy` to the `dev` group in `server/pyproject.toml`. Add
      `[tool.ruff]` with `line-length = 88`. Fix all findings. Run `ruff format`.

- [ ] [63] Add Raw, Source / Rendered and Fullscreen controls to the preview toolbar.

- [ ] [12] Make `static/test-ui.py` run to its end, then fix the three checks that fail:
      the `.pv-content` timeout and the two "edit starts at the top" checks.

- [ ] [*] In `ui/core/state.js`, replace `node.jsonl ? kids : sortKids(kids)` with a
      `node.ordered` flag. Each virtual provider (JSON, JSONL, SQLite) sets the flag.

- [ ] [28] Grow the editor behind the `FS.write` port: undo, find, a line gutter and a
      "modified" mark. Each addition is one file in `ui/editor/`.

- [ ] [27] Try reStructuredText rendering in the browser with Pyodide or a WASM tool,
      behind the rich renderer consent switch. Record size and first-load time in an
      ADR.
    - Depends on: [26]

- [ ] [*] Render `.pptx` in the browser: unzip the file and show the slide text, as one
      registry entry. Then delete `_preview_pptx`, `python-pptx` and `/api/preview`.
    - Depends on: [26]

- [ ] [24] Reduce `app.py` to routing: move `_resolve_safe` and the symlink map to
      `paths.py` and the PWA routes to `pwa.py`. No imports inside functions.
    - Depends on: [33], [34]

- [ ] [33] Keep the URL contract, drop the server-side representations: the server sends
      bytes for `?filemill=raw` and the shell for all else. The client renders the view.
    - Depends on: [32]

- [ ] [35] Decide the fate of the `/w/` named mounts and their CORS middleware: delete
      them, or make CORS opt-in and document it in `SECURITY.md`.
    - Depends on: [32]

- [ ] [32] Render Markdown and `.docx` in the browser in the server edition too. Serve
      the pinned renderer modules from `ui/vendor/`. Then delete `rendering.py` and its
      deps.

- [ ] [34] Make the SQLite provider return JSON only. The client renders tables and rows
      with the JSON hierarchical view. Delete the HTML in `providers/sqlite.py`. Close
      [9].

- [ ] [9] Close the conditional `ViewSpec` proposal: [34] removed the six-argument
      interface.

- [ ] [26] Create one renderer registry, a list of `{kind, render, fallback}`. Both
      editions fill it from the same core list plus their own adapters.

- [ ] [36] Decide how the installed PWA gets a running server: a systemd or launchd
      unit, a launcher, a desktop shell, or only a better "server not running" page.

- [ ] [*] Add a `LICENSE` file with the MIT license text. `README.md` already says MIT.
      Use the current year and "Antti Kaihola" as the copyright holder.

- [ ] [*] Feature: Move to using `pptx-vanilla-viewer` from a CDN for previewing
      PowerPoint files. Current PPTX support was implemented in task
      38ab06e2-c607-4d4a-9978-67847e70d27d.

- [x] [*] Even in non-editing Markdown previews, let the user check/uncheck rendered
      checkboxes and edit the Markdown source to correspond to the checkbox status with
      `- [ ]` or `- [x]`.

- [x] [*] Expand `~/path` links in rendered Markdown to the mount that resolves to
      `$HOME`. Today `[text](~/note.md)` is a dead link although the file exists.

- [x] [38] Fix PPTX previews that show unspaced slide text in both modes.

- [x] [40] Return preview focus to the containing folder and selected file.

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
[37]: docs/tasks/37-pwa-startup-offline-recovery.md
[66]: docs/tasks/66-py-j2-highlighting.md
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
[65]: docs/tasks/65-image-preview-unreliability.md
[67]: docs/tasks/67-scroll-large-directories.md
[68]: docs/tasks/68-server-pytest-fixture-discovery.md
[69]: docs/tasks/69-copy-path-status-cycle.md
[70]: docs/tasks/70-preview-arrow-fullscreen.md
[71]: docs/tasks/71-rst-paragraph-wrapping.md
[72]: docs/tasks/72-mobile-fullscreen-back.md
[73]: docs/tasks/73-markdown-source-highlighting.md
[74]: docs/tasks/74-json-collapse-patterns.md
[75]: docs/tasks/75-standard-column-widths.md
[76]: docs/tasks/76-focused-column-width-stability.md
[*]: TASKS.md

---

[77]: docs/tasks/77-md-tight-bullet-list-line-spacing.md

<!-- hai:reserved-numbers:6,7,9,10,12,13,15,20,21,22,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87 -->

[78]: docs/tasks/78-wide-document-scrolls-instead-of-expanding-the-preview.md

[79]: docs/tasks/79-remove-signs-and-redundant-headings-from-document-section-previews.md

[80]: docs/tasks/80-left-arrow-doesn-t-preview-the-whole-document-after-returning-from-per.md

[81]: docs/tasks/81-horizontal-scrolling-fold-stops.md

[82]: docs/tasks/82-stale-playwright-pins-and-server-renderer-note.md

[83]: docs/tasks/83-screen-reader-search-label-shows-on-screen.md

[84]: docs/tasks/84-json-member-in-archive-shows-chevron-but-does-not-open.md

[85]: docs/tasks/85-images-in-archives-are-not-scaled.md

[86]: docs/tasks/86-markdown-in-archives-is-not-rendered.md

[87]: docs/tasks/87-make-ci-green-so-pages-publishes.md

[88]: docs/tasks/88-status-bar-hints-wrap-and-get-clipped.md

[89]: docs/tasks/89-markdown-previews-show-two-raw-buttons.md

## Rules

Here are the rules for TASKS.md usage:

### TASKS.md maintenance sessions

- In `## Completed / Accepted`, `- [ ] [N] summary` or `- [ ] [*] summary` means
  completed work awaiting user acceptance. `- [x] [N] summary` or `- [x] [*] summary`
  means the user has accepted it. Only user acceptance changes `[ ]` to `[x]`;
  completion, tests and deployment do not.
- Move newly completed issues into `## Completed / Accepted` with `[ ]`.
- During the next maintenance run, remove only `[x]` issues from this section, plus
  their unused description files and reference-style links. Keep `[ ]` issues and any
  files or links still referenced by another issue.
- Each issue must retain either
    - a numbered reference-style link (e.g. `[1]`) to a description file, or
    - `[*]` to indicate no description file is needed for a simple task.
- `[~]` marks an issue that is actively in progress. When the issue is complete, move it
  to `## Completed / Accepted` with `[ ]`, pending user acceptance.
- Link references are listed between `## Completed / Accepted` and `## Rules`.
- Keep summaries concise. Move detailed requirements, rationale, examples and acceptance
  criteria into `docs/tasks/N-issue-description.md`; preserve simple tasks inline. Reuse
  an existing description for the same issue.
- For a new description, use the first unused number, checking both this file and
  description filenames in Git history. Do not reuse numbers of accepted issues.
- The section records work status; the checkbox in `## Completed / Accepted` records
  user acceptance. Completed descriptions retain historical requirements, paths and
  validation results; they are not current implementation instructions. Date later
  corrections and distinguish regressions from earlier work.
- Any completed tasks which haven't yet been moved from `## In Progress` to
  `## Completed / Accepted` should be moved there.
- Any in progress tasks which haven't yet been moved from `## Ordered backlog` or
  `## Scheduled` to `## In Progress` should be moved there.
- Ensure there are no duplicate sections, and that they are in the correct order:
  `## Unverified proposals` -> `## Ordered backlog` -> `## Scheduled` ->
  `## In Progress` -> `## Completed / Accepted` -> `## Rules`.

### Modifying issues

- Ensure dependencies between issues are correctly updated.
- State dependencies using
    - indented `- Depends on: [N]` bullets in TASKS.md, and
    - YAML frontmatter in description files.
- Ensure backlog order respects dependencies.
- When you move an issue, preserve its identifier, text and line wrapping. Change only
  the status checkbox when completion or user acceptance requires it. This keeps moves
  identifiable in Git and reduces avoidable conflicts.

### Workflow for new issue completion

Below, `<filename>@<branch>` means you must operate on the file in the specified branch.

1. Choose issue and schedule work (typically by a heartbeat)

- Pick a backlog issue from `TASKS.md@main`. Pick the first issue that has no dependency
  to any uncompleted issue.
- Move it under `## Scheduled` in `TASKS.md@main` and remove it from
  `## Ordered backlog` and commit `main`.

2. Work on the issue (typically by a task workflow)

- Move the issue under `## In Progress` in `TASKS.md@<worktree-branch>`, ensure no copy
  is left in `## Ordered backlog`.
- Create or update, review and refine a plan in
  `docs/tasks/<N-issue-description>.md@<worktree-branch>`, if more description is needed
  than nicely fits in a bullet point. If you created a plan document, link to it using a
  new `[N]` reference-style link.
- If needed, reword the issue in `TASKS.md@<worktree-branch>` to be more accurate.
- Commit description file (if any) and `TASKS.md@<worktree-branch>`.
- Implement the plan, and lint, test, review and refine the implementation in the
  worktree feature branch.

3. Merge and deploy (typically by last steps of a task workflow)

- Rebase the worktree feature branch on `main` and resolve any conflicts.
- Merge the rebased branch on `main`, and remove the worktree and branch.
- Move the issue from `## In Progress` to `## Completed / Accepted` in `TASKS.md@main`
  with `[ ]`, pending user acceptance, and commit.
- Do any deployment steps if defined in the general development worklow.
