# Technical roadmap

This roadmap closes the gap between `docs/ARCHITECTURE-REVIEW.md` and
`docs/GOALS.md`. Phases are in dependency order. Do them in order. Each phase
is small enough for one task in `TASKS.md`.

Each phase has the same shape:

- **Goal**: what is true when the phase is done.
- **Why now**: why it comes at this point.
- **Steps**: the work, in order.
- **Done when**: checks a person can run.
- **Model**: an open source project that does this well, and what we copy.

The model projects are not chosen for size. They are chosen because each one
does one thing with a discipline we want. Copy the discipline, not the code.

## Phase 0: green and honest

**Goal.** Both test suites are green on `main`. Every document describes the
code as it is. Nothing in the tree is a corpse.

**Why now.** A red suite hides every later regression. Every later phase
depends on being able to trust a green run.

**Steps.**

0. Rebuild the bundle: `cd static && ./build-index.py`. Commit `index.html`.
   Add a pre-commit hook in phase 1 so it cannot go stale again.
1. Delete the HTMX finder completely. Remove from
   `server/src/filemill/app.py`: `click`, `vpage`, `restore`,
   `_finder_fragment`, `finder_root`, `finder_view`, `_build_prune_js`,
   `_make_bc_oob`, `_shell_html`, `_finder_url`. Delete `columns.py`. Delete
   `COLUMN_JS` from `styles.py`, and every CSS rule in `APP_CSS` that only the
   HTMX page used. Delete the HTMX fragments in `providers/sqlite.py:378-419`.
   Delete the 52 failing tests and the substring tests that pin `COLUMN_JS`
   and `APP_CSS`.
2. Fix or remove the `layout=no-columns` directory listing at `app.py:1073`.
   If a no-JavaScript listing is wanted, render a plain list of links to
   root-relative URLs. If not, return the shared shell.
3. Write the decision as a one-page ADR in `docs/adr/0001-one-finder.md`:
   the shared UI owns all interaction; the server renders documents and JSON.
   This closes proposal [8] in `TASKS.md`.
4. Fix the JSON key-order bug. Replace `node.jsonl ? kids : sortKids(kids)`
   in `ui/core/state.js:36` with an explicit `node.ordered` flag that every
   virtual provider sets. Make `static/test-ui.py` run to its end: wrap each
   section so that one thrown `await` fails a check instead of the run. Then
   find the cause of the `.pv-content` timeout at `test-ui.py:1012` and the
   two "edit starts at the top" failures.
5. Correct the documents that finding 15 of the review lists:
   `server/README.md`, `server/CONTRIBUTING.md`, `server/TASKS.md`,
   `docs/tasks/2-fix-all-test-failures.md`, and the completed item for the
   editor cursor in root `TASKS.md`.
6. Add `LICENSE` with the MIT text. `README.md` already claims it.
7. Delete `static/hotreload.py`, `forgetRoots` in `ui/adapters/storage.js`,
   `PYGMENTS_FORMATTER` and the duplicate `FRIENDLY_CSS` in `styles.py`.

**Done when.** `cd server && uv run pytest` passes. All of
`static/test-ui.py`, `test-url.py` and `test-rich.py` pass in both `--dev`
and bundle mode. CI on `main` is green. `grep -r htmx server/src` finds
nothing.

**Model.** SQLite: trunk is never left red, and every fix lands with its
test. Zig, before 1.0: when a design is replaced, the old code leaves in the
same change, so two implementations never live side by side.

## Phase 1: gates

**Goal.** A formatting or lint error cannot be committed or merged.

**Why now.** Every later phase moves a lot of code. Automatic formatting
removes style from review and leaves only substance.

**Steps.**

1. Add `ruff` and `mypy` to the `dev` dependency group. Add `[tool.ruff]`
   with `line-length` and `target-version`. Fix the 58 ruff findings and
   format the 10 files.
2. Remove every `# noqa: S608` in `providers/sqlite.py`. Quote identifiers
   with double quotes and escape `"` as `""`, or validate the name against
   `sqlite_master` before use.
3. Add a JavaScript formatter and linter that need no Node project. Biome as
   one binary from Nix, or `deno fmt` and `deno lint`, both work on plain
   files. Pick one and pin it. Format `ui/` once.
4. Add `.pre-commit-config.yaml` with ruff, ruff-format, mypy and the
   JavaScript tool.
5. Add a `lint` job to `.github/workflows/publish.yml` that runs before the
   tests.
6. Turn coverage off by default in `pytest.ini_options` and on in CI. A
   single-test run must be fast.

**Done when.** `pre-commit run --all-files` passes. The CI `lint` job passes.
No `# noqa` exists without a link to an issue.

**Model.** Ruff and uv: one fast tool, pinned, in CI. Go: `gofmt` made
formatting a non-discussion from the first release. We want the same silence.

## Phase 2: one source of truth for documents

**Goal.** Each fact lives in one document. Every document is in Simplified
Technical English. There are fewer lines of prose than lines of code.

**Why now.** The next phases change the shape of the code. The documents
must be small enough to update in the same commit.

**Steps.**

1. Merge `server/TASKS.md`, `server/ISSUES.md` and `static/TASKS.md` into
   root `TASKS.md` and `docs/tasks/`. Keep the open items. Delete the closed
   ones; git keeps their text.
2. Delete `server/PLAN-18.md`, `PLAN-19.md`, `PLAN-20-shared-frontend.md` and
   `server/lmt/`. If a paragraph in them is still true and not elsewhere,
   move that paragraph, not the file.
3. Delete `server/.pi/settings.json`, `server/mobile-narrow-preview.png`,
   `server/.claude/commands/` and `architecture-review-20260904.html`.
   `docs/ARCHITECTURE-REVIEW.md` covers the last one.
4. Make root `README.md` the one explanation of the two editions and the
   ports. `server/README.md` and `static/AGENTS.md` link to it and keep only
   what is specific to their edition.
5. Create `docs/adr/`. Split the decisions table in `static/AGENTS.md` into
   one dated file per decision, in the format: context, decision, measurement,
   consequences. Keep each under 40 lines.
6. Add root `CONTRIBUTING.md` (setup, tests, commit style, the STE rule),
   `SECURITY.md` (threat model and how to report) and `CHANGELOG.md` (Keep a
   Changelog format).
7. Rewrite the documents that remain in Simplified Technical English.

**Done when.** `git ls-files '*.md' | xargs wc -l` is below the line count of
`*.py`, `*.js` and `*.css` together. Every claim in a document can be checked
against the code by a `grep`.

**Model.** curl: `docs/` is a product, with `SECURITY.md`, `CONTRIBUTE.md`
and a changelog per release. Django: documents change in the same commit as
the code, and old behaviour has a written deprecation path.

## Phase 3: make the shared UI a module graph

**Goal.** `ui/core/` can be imported without an HTML file, without a DOM
order and without any adapter. The dependency graph is explicit.

**Why now.** This is the prerequisite for native shells and for every later
UI change. It is also where most hidden coupling lives.

**Steps.**

1. Convert every file in `ui/core/` and `ui/adapters/` to an ES module with
   `import` and `export`. Add one entry module per edition:
   `ui/entry-static.js` and `ui/entry-server.js`.
2. Make `static/build-index.py` inline modules. The simplest form is one
   `<script type="module">` that contains the concatenated graph in
   topological order with import and export lines removed. Keep the
   `--check` mode.
3. Delete the script lists in `static/index-dev.html` and
   `server/src/filemill/app.py`. Each page loads one entry module.
4. Break the cycles. `render.js` receives the callbacks it wires
   (`choose`, `unfoldTo`, `refreshColumn`) as one `actions` object at boot.
   `layout.js` gets `set` and `setVar` from a small `dom.js`.
5. Move adapter code out of `core/`. Move `jsonl.js` to
   `adapters/vfs-json.js`. Move the welcome screen and "Open Folder" markup
   from `shell.js` to `app-fsa.js`. Move the local badge and "leave local"
   control to `app-http.js`. Move `offerRichToggle` from `settings.js` to
   `preview-rich.js`.
6. Document the full port contract in `ports.js`: `FS.node`, `FS.blob`,
   `ROUTER.write(state, replace)`, `RouterPath.base`, and every node field.
   A field not in the list is a bug.
7. Create `core/limits.js` with one `TEXT_MAX` and one image extension list.
   Delete the other four copies. Create one `mountRoot()` in `core/` and one
   `currentPath()`; delete `pathParts`.
8. Merge `withJsonl` and `withJson` into one `withVirtual(fs, spec)`.

**Done when.** `grep -n "vpath\|showDirectoryPicker\|PreviewLocal\|API\b" ui/core/`
finds nothing. `static/build-index.py --check` passes. A Node or Deno script
can `import` `ui/core/sort.js` and call `sortKids` with no DOM.

**Model.** Lua and Redis: one concept per file, and every file can be read
on its own. Zig: no hidden globals; what a file uses, it names.

## Phase 4: state and render discipline

**Goal.** A render is cheap and predictable. The preview is fetched once per
selection. Every number has a name.

**Why now.** Phase 3 has made the graph visible. Now fix what it shows.

**Steps.**

1. Cache the preview element keyed on the previewed node and its `meta`, in
   the same way `colCache` keys columns. A render with the same key reuses
   it. Add a check in `test-ui.py` that a resize causes zero calls to
   `PREVIEW.render`.
2. Replace `cursor[i]`, `sel[i]` and `node.lastSel` with one selection model:
   `sel[i]` is the selected name; the row index is derived when needed.
3. Split `applyScroll` (`layout.js:43-118`) into `foldFromScroll`,
   `applyWidths`, `panFocus` and `slideTail`. Each is under 25 lines.
4. Name every magic number in `state.js`, `layout.js`, `nav.js` and
   `render.js`, and say in one line why the value is what it is.
5. Give the narrow-screen layout a written model in `docs/adr/`: what folds,
   what pans, what is promised to stay on screen. Add one test per device
   class (phone portrait, phone landscape, tablet, desktop).

**Done when.** The render budgets in `test-ui.py` are unchanged or better.
The preview fetch count per resize is zero. `applyScroll` is gone.

**Model.** SQLite: every performance claim has a test that would fail if the
claim stopped being true.

## Phase 5: one file kind and one order

**Goal.** "What kind of thing is this entry?" and "in what order do entries
appear?" are each answered in one place per side.

**Why now.** Proposals [6] and [7] in `TASKS.md` describe this. They were
correct on 2026-09-04 and are still open. They are small once phase 3 is
done.

**Steps.** Follow `docs/tasks/6-file-kind-classification.md` and
`docs/tasks/7-adapter-owned-entry-order.md`. Add one test table per language
that both sides share by value.

**Done when.** The acceptance criteria in those two files hold.

## Phase 6: a minimal server

**Goal.** The Python server does only what a browser cannot: list a
directory, serve bytes, save a file, read SQLite and serve the shell. Every
renderer that has a browser implementation runs in the browser, in both
editions. `app.py` is routing only.

**Why now.** Most of the Python dates from the HTMX finder, when the server
built every fragment. The shared UI already renders text, source, images,
PDF, HTML, JSON and JSONL itself, and renders Markdown and `.docx` in the
static edition. Two render paths for one document drift apart.

**Steps.**

1. Serve the pinned Markdown and `.docx` renderer modules from `ui/vendor/`
   so the server edition needs no CDN and no consent. Port the wikilink and
   relative-link rules and their tests from `rendering.py`. Delete
   `rendering.py`, `_preview_md`, `_preview_docx` and the `markdown-it-py`,
   `mdit-py-plugins`, `linkify-it-py`, `pygments` and `mammoth` dependencies.
2. Keep the URL contract in `urls.py` (`?filemill=`, `?layout=`). The server
   answers `raw` with bytes and everything else with the shell. The client
   reads `data-filemill` and `data-layout` and shows the source view or the
   preview-only layout. Delete `_view_switch_html`, `_representation_html`,
   `_document_page` and `render_source`.
3. Make the SQLite provider return JSON only. The client shows tables and
   rows with the JSON hierarchical view. Delete `render_preview` and the two
   HTML renderers in `providers/sqlite.py`. This closes proposal [9].
4. Delete what the browser already does: `/api/render` and
   `preview-upload.js`, `/open-link`, `/sse/reload` and live reload,
   `providers/json_provider.py`, `providers/csv_provider.py`, `styles.py`
   and `/raw?path=`. Decide `/w/` and its CORS middleware with its consumer.
5. Reduce `app.py` to routing. Move `_resolve_safe` and the symlink map to
   `paths.py` and the PWA routes to `pwa.py`. Compute the symlink zone map
   once per request. Default `--bind` to `127.0.0.1`.
6. Replace `python-fasthtml` with `starlette` and `uvicorn`. The shell is one
   string template.
7. Apply `docs/tasks/9-vfs-viewspec.md` only if step 3 has not made it moot.

**Done when.** `dependencies` in `server/pyproject.toml` lists `starlette`,
`uvicorn`, `typer` and `python-pptx` only. The line count of
`server/src/filemill/**/*.py` is under 1 500. No function-local imports.
`grep -rn "raw?path\|open-link\|sse/reload" server/src` finds nothing. The
same Markdown file shows the same HTML in both editions.

**Model.** Redis: one file per subsystem, and the entry point is short.
`python -m http.server`: a server that serves files can be very small.

## Phase 7: one test harness

**Goal.** One command runs every test. A failure names its check. No test
waits for a fixed time.

**Steps.**

1. Move `static/test-ui.py`, `test-url.py` and `test-rich.py` under
   `pytest` with fixtures for the fake handle, the OPFS root and the served
   bundle. Split the 1 529-line `main()` into one function per section.
2. Replace every `wait_for_timeout` with `wait_for_function` or `expect`.
3. Run the static and server browser tests through one `conftest.py` and one
   Playwright fixture. Delete the proxy plumbing in
   `test_browser_keyboard.py`; nothing loads from a CDN any more.
4. Keep `test-e2e.py` as a documented manual check in
   `static/FSA-TEST-CHECKLIST.md`.
5. Make `conftest.py` stop mutating the module global `ROOT`, so the suite
   can run with `-n auto`.

**Done when.** `uv run pytest` at the repository root runs everything. No
`wait_for_timeout` remains. The suite runs in parallel.

**Model.** SQLite: the tests are the product's strongest claim. Playwright's
own suite: assert on conditions, never on clocks.

## Phase 8: preview and editing to world class

**Goal.** Preview and editing are a table, not a ladder, and the table is the
same in both editions.

**Steps.**

1. Create one renderer registry: a list of `{kind, render, fallback}`. Both
   editions fill it from the same core list plus their own adapters.
2. Implement CSV as a browser virtual filesystem (issue #49), `.mp4`
   preview, and a browser `.pptx` renderer. When `.pptx` renders in the
   browser, delete `python-pptx` and `/api/preview`.
3. Try reStructuredText in the browser with a small Pyodide or WASM
   experiment behind the existing consent switch. Record the size and the
   first-load time in an ADR before deciding.
4. Grow editing behind the same `FS.write` port: undo, find, a line gutter,
   and a "modified" mark. Each addition is one file in `ui/editor/`.

**Done when.** Adding a preview kind is one entry in one table plus one test.

## Phase 9: native shells

**Goal.** One native shell runs the same core with native ports.

**Steps.**

1. Define `ui/core/` as a model package with no DOM: nodes, selection,
   folding arithmetic, keyboard map, deep links. Keep a thin DOM renderer
   beside it.
2. Prototype one shell that hosts the DOM renderer in a WebView and supplies
   the three ports natively. Tauri or the platform WebView both work. Choose
   by the smallest binary that passes the test suite.
3. Only then evaluate fully native toolkits (AppKit, GTK, WinUI). Record the
   comparison in an ADR.

**Done when.** The prototype passes `test-ui.py` through its native `FS`
port.

## How we keep it this way

- Every change updates the documents in the same commit.
- Every decision that changes a port or a behaviour gets an ADR the same day.
- Documents and comments use Simplified Technical English.
- Delete what you replace, in the same change.
- A renderer lives in `ui/`, not in Python, unless the browser cannot do it.
- No `# noqa` and no skipped test without a link to an issue.
- A red suite blocks every merge. No exceptions.
