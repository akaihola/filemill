# Technical roadmap

This roadmap closes the gap between `docs/ARCHITECTURE-REVIEW.md` and
`docs/GOALS.md`. Phases are in dependency order. Do them in order. Each phase
is small enough for one task in `TASKS.md`.

## Status index, 2026-10-19

There are ten phases, 0–9. Status below starts from [102]'s audit of main
`26a77d60` on 2026-10-18 and includes later main through `25bc4d4e`, plus
[93]/[94]'s CI delivery at `7da2e69`.
See [the audit](tasks/102-audit-the-technical-roadmap-against-main-and-draft-the-next-phase-s-is.md)
for every step's evidence. [105] corrects edition/renderer guidance; [106]
closes the suppression/obsolete-skip check; [103]/[104] resolve A1–A3.
[108] adds condition-based keyboard scroll waits.

The original goals, steps and checks below remain the policy record. Paths,
commands and assertions in delivered or superseded steps describe their old
baseline; use [CONTRIBUTING.md](../CONTRIBUTING.md) for current commands.
The open checks below still name `static/test-ui.py`, `test-url.py` and
`test-rich.py`. Since `587752b4` (2026-10-17) these are
`static/tests/test_ui.py`, `test_url.py` and `test_rich.py`, run with
`--bundle`, `--dev` or `--native`.
The architecture review takes precedence when its remediation order conflicts
with this sequence. Remaining work uses bounded issues. Local validation does
not establish remote CI or user acceptance.

The one-task-per-phase policy above remains pending Antti's decision. Its
size claim fails: Phases 0 and 1 already span [93]/[94], [105], [106] and
[107]. The under-40-line ADR and four-dependency/1,500-line server policies
also remain; their failed checks are explicit in Phases 2 and 6.

Each phase has the same shape:

- **Goal**: what is true when the phase is done.
- **Why now**: why it comes at this point.
- **Steps**: the work, in order.
- **Done when**: checks a person can run.
- **Model**: an open source project that does this well, and what we copy.

The model projects are not chosen for size. They are chosen because each one
does one thing with a discipline we want. Copy the discipline, not the code.

## Phase 0: green and honest

Status 2026-10-19: Partly done. Steps 0–4, 6 and 7 are implemented. ADR 0067 retires
step 2's layout. [105] and [107] correct step 5's current/historical claims;
the task 2 file and editor-cursor item are already retired, with dated
corrections in [107]. [109] corrects the remaining stale claims in
`server/README.md` and `server/CONTRIBUTING.md` (2026-10-19). [99]/[101]
record green local suites. [93]/[94] now record
[green main CI and Pages deployment](https://github.com/akaihola/filemill/actions/runs/39318918168)
at `7da2e69`, closing Phase 0's delivery check. A11's final documentation
command audit remains open.

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
   `COLUMN_JS` implementation, and every CSS rule that only the
   HTMX page used. Delete the HTMX fragments in `providers/sqlite.py:378-419`.
   Delete the 52 failing tests and the substring tests that pin `COLUMN_JS`
   implementation.
2. Fix or remove the `layout=no-columns` directory listing at `app.py:1073`.
   If a no-JavaScript listing is wanted, render a plain list of links to
   root-relative URLs. If not, return the shared shell. Done for issue 33: the
   shell is returned. On 2026-09-25 the layout itself was removed
   ([ADR 0067](adr/0067-drop-no-columns-layout.md)).
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
   the unused Pygments formatter and duplicate friendly CSS definitions.

**Done when.** `cd server && uv run pytest` passes. All of
`static/test-ui.py`, `test-url.py` and `test-rich.py` pass in both `--dev`
and bundle mode. CI on `main` is green. `grep -r htmx server/src` finds
nothing.

**Model.** SQLite: trunk is never left red, and every fix lands with its
test. Zig, before 1.0: when a design is replaced, the old code leaves in the
same change, so two implementations never live side by side.

## Phase 1: gates

Status 2026-10-19: Partly done. Steps 1–6 are implemented. [106] removes the six
unlinked suppressions and obsolete PPTX skip identified by [102], and adds a
Python suppression-link guard to the existing gate. Its gate has seven hooks after adding the guard.
[CONTRIBUTING.md](../CONTRIBUTING.md#tests) describes the gate, its pins and
what local hooks do not prove. [93]/[94] record the green delivered-main run.
Installation of local hooks and enforced branch protection remain unproven.

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

Status 2026-10-19: Partly done. Steps 1, 2 and 6 are implemented. [105] consolidates
shared edition facts; [107] dates superseded claims. Duplication and unchecked
claims remain under 3 and 7. Step 4 is absent from the original numbering.
The under-40-line ADR policy remains and fails: [102] measured fourteen ADRs
at least 40 lines, including ADR 0064 at 162. Before this patch, later main
has sixteen such ADRs, including new ADRs 0081/0082. Preserve measurements
while the policy decision is pending. [102]'s prose/code line ratio passes.

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
3. Make root `README.md` the one explanation of the two editions and the
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

Status 2026-10-19: Partly done. Steps 1–5, 7 and 8 are implemented; step 6 misses
some node fields. The DOM-free package is now `ui/core/model/`, where
`sortKids` can be imported from `ui/core/model/sort.js`. The `grep` check
below needs `-r` to search the directory. Core vpath checks and HTTP search
coupling remain; [102] records passing bundle and acyclic-module checks.

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

Status 2026-10-19: Partly done. Steps 2, 3 and 5 are implemented; step 1's preview
reuse is open and step 4's constants cleanup is partial. `applyScroll` remains
the coordinator of the four extracted helpers. A9 and ADR 0079 record preview
recreation and native resize cost. Splitting helpers did not satisfy the
literal `applyScroll` deletion check.

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

Status 2026-10-19: Done implementation. [6]/[7] implement classification tables and
adapter-owned order, including descending name order. Their "still open"
wording below is historical. This does not imply user acceptance of related
tracker entries.

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

Status 2026-10-19: Partly done. Steps 3, 6 and conditional step 7 are complete;
steps 1, 2, 4 and 5 retain work. Markdown/DOCX use vendored browser modules;
RST and archive consumers still use the preview API. [129] removed `/w/`
and `/n/` aliases on 2026-10-20; file addresses are root-relative. Do not
restore the removed upload renderer or the browser live reload over `/sse/reload` (`cb453a00`). `filemill --live` is Uvicorn's
reload and stays.

The original budgets remain and fail. [102] measured 2,491 production Python
lines; main through `25bc4d4e` has 2,597, counting all `.py` direct children
and descendants of `server/src/filemill/`. The target is below 1,500.
`server/pyproject.toml` lists six runtime dependencies: starlette, uvicorn,
pygments, docutils, typer and conditional zstandard. This fails both the
four-dependency count and the named set below; python-pptx is now test-only.
Two function-local zstandard imports remain for Python compatibility, failing
the zero-local-import check. These failures await a policy decision; this
status note does not waive them or authorize deleting supported behavior.

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
   compressed columns. Delete `_view_switch_html`, `_representation_html`,
   `_document_page` and `render_source`.
3. Make the SQLite provider return JSON only. The client shows tables and
   rows with the JSON hierarchical view. Delete `render_preview` and the two
   HTML renderers in `providers/sqlite.py`. This closes proposal [9].
4. Delete what the browser already does: `/api/render` and
   `preview-upload.js`, `/sse/reload` and live reload,
   `preview-upload.js`, `/sse/reload` and live reload,
   `styles.py`
   and `/raw?path=`. The `/w/` route and its mount helpers were removed in [129].
5. Reduce `app.py` to routing. Move `_resolve_safe` and the symlink map to
   `paths.py` and the PWA routes to `pwa.py`. Compute the symlink zone map
   once per request. Default `--bind` to `127.0.0.1`.
6. Replace `python-fasthtml` with `starlette` and `uvicorn`. The shell is one
   string template.
7. Apply `docs/tasks/9-vfs-viewspec.md` only if step 3 has not made it moot.

**Done when.** `dependencies` in `server/pyproject.toml` lists `starlette`,
`uvicorn`, `typer` and `python-pptx` only. The line count of
`server/src/filemill/**/*.py` is under 1 500. No function-local imports.
`grep -rn "raw?path\|sse/reload" server/src` finds nothing. The
same Markdown file shows the same HTML in both editions.

**Model.** Redis: one file per subsystem, and the entry point is short.
`python -m http.server`: a server that serves files can be very small.

## Phase 7: one test harness

Status 2026-10-19: Partly done. Steps 1, 2 and 4 are implemented; 3 and 5 remain
partial. [25]/[99] move the old static scripts into `static/tests/` and root
pytest; [99]/[101] record passing root, bundle and dev suites. No fixed browser
waits remain. Separate browser lifecycles persist, and a root `pytest -n auto`
pass is not established. Parallel CI suites do not prove it.

**Goal.** One command runs every test. A failure names its check. No test
waits for a fixed time.

**Steps.**

1. Done in [25]. Static checks live under `static/tests/` with pytest
   fixtures for the fake handle, OPFS root and served bundle. Each former
   `main()` section is a separate test. Root `uv run pytest` runs both editions.
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

Status 2026-10-19: Requested implementations in steps 1–4 are done. Registry,
CSV/video/browser PPTX text extraction, RST evaluation and editor modules
exist. Step 2's unconditional preview-API removal is overtaken by RST/VTT
and archive consumers. Full office fidelity remains a product goal; save
atomicity/conflicts remain A4 work. Browser-owned RST routing remains A8.

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

Status 2026-10-19: Prototype steps 1–3 are done. [29] supplies the model;
[30]/ADR 0079 qualify WebKitGTK; [31]/ADR 0066 retain WebView over widgets.
ADR 0079 records 220 UI checks passing in 4/5 runs and remaining native limits.
This is a Linux prototype. Cross-platform application release parity remains
future work.

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
- Every `# noqa` needs a link to an issue. A test for supported behavior that
  is disabled because it is broken or unfinished also needs an issue link.
- A platform or optional-tool prerequisite skip needs an explicit reason, but
  no defect issue. The Linux pipe-capacity regression in the [keyboard browser
  tests] may skip on other platforms. The [Git bundle browser test] and
  [Git bundle provider tests] may skip when Git is missing, because Git bundle
  support is optional. These three skips describe prerequisites, not defects.
- CI must supply required prerequisites and run all applicable checks. For
  example, Linux CI testing Git bundle support must have Git and run these
  checks. Do not omit dependencies to obtain a misleading pass.
- A red suite blocks every merge. No exceptions.

[keyboard browser tests]: ../server/tests/test_browser_keyboard.py
[Git bundle browser test]: ../server/tests/test_browser_new_ui.py
[Git bundle provider tests]: ../server/tests/test_gitbundle_provider.py
[129]: tasks/129-remove-the-obsolete-w-and-n-url-routes.md
