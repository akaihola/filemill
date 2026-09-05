# Architecture review, 2026-09-05

This review measures the code against `docs/GOALS.md`. It replaces the review
of 2026-09-04 (`architecture-review-20260904.html`), which it also reviews in
its last section. `docs/ROADMAP.md` turns the findings into ordered work.

## How to read this review

- **Scope.** Every file in `ui/`, `server/src/`, `static/`, the tests and the
  documents was read. Both test suites were run on branch
  `feature/in-the-repository-do-tf9` at commit `eae2a6d`.
- **Severity.** Each finding has one of four levels, the same scale the
  previous review used:
  - **Blocker**: the project cannot claim to be healthy until this is fixed.
  - **Strong**: a real defect or duplication with evidence in the code.
  - **Worth exploring**: a likely improvement that needs a decision first.
  - **Speculative**: an idea with no failure to show yet.
- **Evidence.** Each finding names a file and a line. Line numbers are for the
  commit above. A finding marked "not verified" was reported by a read of the
  code but not reproduced by a run.
- **Tone.** This review is direct because the goals are high. The project is
  small, well reasoned and unusually well explained. The gap to world-class
  is real, but it is a gap of discipline, not of design.

## What is healthy

Keep these. They are the parts of the project that already meet the goals.

- **Three ports, one core.** `ui/core/ports.js` declares `FS`, `PREVIEW` and
  `ROUTER`. Two adapters exist for each. `ui/core/deeplink.js` is shared
  without change between editions.
- **One shared frontend.** `ui/` is a symlink into the Python package. There
  is no copy that can go stale. `docs/tasks/3-remove-duplicate-ui-source.md`
  explains why the symlink points this way.
- **Decisions recorded with numbers.** The decisions table in
  `static/AGENTS.md` gives the measurement behind each choice. Few projects
  of any size do this.
- **Real filesystem tests without a dialog.** `static/test-url.py` builds
  3 000 files in the origin private file system and runs the real adapter
  against them.
- **The virtual filesystem seam.** `server/src/filemill/vfs.py` is a small
  protocol, and three providers implement it.
- **The bundle cannot silently go stale.** `static/build-index.py --check`
  fails in CI when `index.html` does not match `ui/`.
- **The wheel excludes what the server never loads.** `pyproject.toml`
  explains why, and a test depends on it.

## Findings

### 1. Both test suites are red (Blocker)

**Server.** `cd server && uv run pytest -m "not integration" --no-cov` gives
52 failed, 754 passed. Commit `0cae978` removed the route decorators of the
HTMX user interface (`/f/`, `/click`, `/vpage`, `/restore`). It did not remove
the handlers, `columns.py`, the 548-line `COLUMN_JS` string in `styles.py`, or
the tests that call those routes. Every failure is a test that expects 200
and receives 404.

**Static.** `cd static && uv run --with "playwright==1.61.0" python3 test-ui.py --dev`
prints 79 passed and 3 failed, then stops with a Playwright timeout at
`static/test-ui.py:1012`. About 90 later checks never run. The failed checks:

| Check | Observed |
| --- | --- |
| Valid JSON opens as an ordered key column | keys sorted, not in file order |
| Plaintext edit starts at the top | cursor at 0, `scrollTop` 6755 |
| Highlighted edit starts at the top | cursor at 0, `scrollTop` 21005 |

**Bundle.** `cd static && ./build-index.py --check` fails: the committed
`index.html` is behind `ui/` by two source changes (the editor cursor fix and
the unfold-on-left fix). CI runs this check first, then both suites
(`.github/workflows/publish.yml`), so CI is red three times over.

**Why it matters.** A red suite hides the next regression. It also makes the
documents wrong: `docs/tasks/2-fix-all-test-failures.md` says 870 passed, and
`server/README.md` says `uv run pytest` works.

### 2. The HTMX finder is half deleted (Blocker)

The routes are gone. The code is not. `server/src/filemill/app.py` keeps
`click` (233-352), `_finder_fragment` (409-530), `vpage`, `restore`,
`finder_root`, `finder_view`, `_build_prune_js`, `_make_bc_oob` and
`_finder_url`. `columns.py` (346 lines) and `styles.py:COLUMN_JS` exist only
for them. `providers/sqlite.py:378-419` renders HTMX pagination bars nobody
can reach. This is about 1 500 lines of Python and 1 500 lines of tests.

`app.py:1073` still calls `list_column()` for a directory with
`layout=no-columns`. That page emits links to `/click`, which is 404, loads no
htmx, and writes the absolute host path of the directory into the HTML.

The previous review asked for a decision before this deletion
(`docs/tasks/8-consolidate-finder-stacks.md`). The decision was made in code
one day later and was never written down.

### 3. The JSON key order bug (Strong, verified)

`ui/core/state.js:36` exempts only nodes with `jsonl: true` from sorting.
`ui/core/jsonl.js:123-127` marks JSON nodes with `json: true`, not `jsonl`.
`ui/core/sort.js:66-72` then puts containers first and sorts by name. A file
`{"name","tags","meta"}` renders as `meta, tags, name`. Introduced in
`b4eb70c`. The fix is one explicit flag, `ordered`, that every virtual
provider sets, and one check in `visibleKids`.

### 4. The shared UI has no module system (Strong)

Every file in `ui/` is a classic `<script>`. Every top-level name is a global.
The load order is the dependency graph, and it is written twice:
`static/index-dev.html:18-38` and `server/src/filemill/app.py:718-730`.
Nothing checks that the two lists agree.

Real cycles exist. `render.js:49-69` calls `unfoldTo`, `refreshColumn` and
`choose`, which `nav.js` defines 350 lines later. `layout.js` uses `set` and
`setVar` from `render.js`, and `render()` calls `layout()`. `state.js:36`
calls `sortKids` from a file that loads after it.

Core knows adapter facts. `render.js:254` tests `n.vpath`, a server concept.
`shell.js:24-26,83-93` builds the welcome screen, the "Open Folder" button
and the local badge, which belong to one adapter. `settings.js:38-43` exists
for `preview-rich.js` alone. `core/jsonl.js` wraps ports and reads file
extensions; it is an adapter that lives in `core/`.

Adapters share globals with each other. `preview-http.js:27` and
`preview-upload.js:35` use `API` from `http.js:12`. Three adapters call
`PreviewLocal` directly.

**Why it matters.** The native shells in `docs/GOALS.md` need a core that
can be imported without a DOM and without the other adapters. Today the core
cannot be loaded at all without the exact script order of one HTML file.

### 5. The port contract is a third of the real interface (Strong)

`ui/core/ports.js` declares `FS.ensureLoaded`, `FS.loadMeta`, optional
`FS.write`, `PREVIEW.render`, optional `PREVIEW.revoke`, `ROUTER.read`,
`ROUTER.write(state)` and `ROUTER.onNavigate`. The code also requires:

- `FS.node(name, …)`, called by both entry points with an adapter-specific
  second argument.
- `FS.blob(node)`, called from `render.js`, `jsonl.js` and four adapters.
- A second argument `replace` on `ROUTER.write`, passed by `deeplink.js:41`
  and implemented by both routers.
- `RouterPath.base`, read by `app-http.js:68`.
- About fifteen node fields: `loading`, `denied`, `meta`, `metaDone`,
  `metaLoading`, `metaPending`, `metaSwept`, `lastSel`, `file`, `handle`,
  `rel`, `vpath`, `icon`, `jsonl`, `json`, `value`, `record`, `jsonError`.
  Four are documented.

`HTTP.loadMeta` (`http.js:65-67`) writes `{error}` for any file without
metadata, and `fillPreview` (`render.js:212`) then never calls
`PREVIEW.render`. A stat failure silently removes a preview that would
render. Not verified by a run.

### 6. The preview is rebuilt on every render (Strong)

`render.js:162` calls `renderPreview()` on every `render()`. There are 23
call sites of `render()`. A resize, a font load, a sort sweep or a settings
change therefore builds a new preview element. Each one calls
`PREVIEW.revoke()`, then `FS.loadMeta` again, then `PREVIEW.render` again. On the server
edition that is a new `GET /api/preview`. `editableText` (`render.js:253-264`)
runs on the same path and re-reads and re-decodes the whole file each time.
Columns are cached with care (`render.js:4-9`); the preview is not.

### 7. Duplication in the shared UI (Strong)

- `512 * 1024` appears five times under four names: `TEXT_MAX`,
  `JSONL_MAX`, `JSON_MAX`, `EDIT_MAX`, and a literal in `preview-rich.js:126`.
- The image extension list appears in `preview-local.js:19`,
  `preview-upload.js:25` and `render.js:251`. A comment at `render.js:246-249`
  asks a human to keep two of them in step.
- The mount preamble appears in `app-fsa.js:64-70`, `app-http.js:42-47` and
  `app-http.js:62-70`.
- `nav.js:158 pathParts` and `deeplink.js:22 currentPath` build the same path
  and disagree about the root and about empty leaves.
- `withJsonl` and `withJson` in `jsonl.js:75-197` are one shape written twice,
  and so are their two preview tables.

### 8. Mobile and tablet are arithmetic, not design (Worth exploring)

`ui/core/styles.css` has no media query except `prefers-reduced-motion`.
There are no touch or pointer handlers. Narrow screens are handled by clamps
spread over `state.js:72-75`, `render.js:135`, `layout.js:29-37` and
`layout.js:104-113`, with measured cases (390 px, 376 px, 292 px) in
comments. The one clean part is that folding rides native horizontal scroll,
so touch scrolling works without code. There is no named breakpoint and no
phone-specific test except a viewport resize in `test-ui.py:839`.

The goal is a file manager for tablets and phones. The current code reaches
phones by accident of arithmetic. It needs a written layout model with a test
per device class.

### 9. Preview and editing (Worth exploring)

Preview kinds are dispatched by regular expressions on the file name inside
each provider. There is no table. Providers are stacked as decorators at boot
(`app-fsa.js:14`, `app-http.js:33`), four levels deep, each with an `if`
ladder. Adding one kind means editing a ladder.

Editing exists and works: `render.js:253-301` gates on `FS.write`, file kind,
size, UTF-8 and line length, and both adapters implement `write`. It is one
text area with Save and Cancel. The goal says "world-class editing". The
distance is large and should be planned, not patched.

### 10. Server structure (Strong)

`app.py` (1 203 lines) holds too much. It has routing, the security
primitive, three URL builders and two page shells. It also has the API glue,
the PWA routes, CORS middleware and a route reorderer. Coverage on it is
62 %, because a third of it is dead.

Cycles are hidden by function-local imports. `columns.py:86` imports from
`app`. `rendering.py:103` imports `app` to reach two private names,
`_rel_url_path` and `_web_url`. `preview.py:157` imports `rendering` lazily.
Three modules therefore form a ring that only import order keeps alive.

`styles.py:4-5` defines `HIGHLIGHT_CSS` and `FRIENDLY_CSS` with identical
values and emits both. `styles.py:3 PYGMENTS_FORMATTER` is never used.
The `<div class="preview-error">` fragment is built by hand in nine places
across `app.py`, `api.py`, `preview.py` and `sqlite.py`.

### 11. The virtual filesystem seam (Worth exploring)

`VFSProvider.render_preview(path, vpath, fmt, page, limit, col)` has six
parameters. `fmt`, `page` and `limit` matter only to SQLite; `col` matters
only to the deleted HTMX finder. Registration is an import side effect at
`vfs.py:79-81`, and the order matters. "Is this file a folder?" is answered
in three ways: `vfs.is_vfs_file`, `api._opens_as_folder` (which lists the
entries to find out) and `api.split_vfs` (which special-cases `.jsonl`).
`.jsonl` and `.json` are virtual filesystems in the browser with no server
provider. The CSV provider is a stub (issue #49). The proposal in
`docs/tasks/9-vfs-viewspec.md` is still correctly gated.

### 12. Security (Strong)

The threat model is a local tool, so none of these is an emergency. They are
listed because a world-class project writes them down.

- `preview.py:216,225,231` embed `src="/raw?path=<absolute path>"` in
  fragments sent to the browser. `api.py:12-16` says no request shape names
  an absolute path. Both cannot be true.
- `/w/` answers with `Access-Control-Allow-Origin: *` (`app.py:1131`) and the
  server binds to `0.0.0.0` by default (`cli.py:18`). Any page on the network
  can read any file under the root. No document says so.
- Table names from the URL are quoted as `[{table}]` in
  `providers/sqlite.py` under eleven `# noqa: S608`. A `]` in a name breaks
  the quoting. The read-only connection limits the effect to the same file.
- Any `.html` under the root is served same-origin and can call
  `POST /api/save`.
- `_resolve_safe` (`app.py:71-112`) lists the root on every call, and three
  other functions walk the root again for symlinks.

### 13. Tests (Strong)

- Server: 629 tests in 17 files. About 500 lines of `test_rendering.py` and
  much of `test_app.py:280-800` assert that a string contains a string, for
  example `"'PageUp'" in COLUMN_JS`. They pin dead JavaScript.
- Static: four standalone scripts and no runner. `test-ui.py` is one function
  of 1 529 lines with 169 checks and 168 fixed waits. One thrown `await`
  stops the run, as finding 1 shows. `test-e2e.py` needs a human and is not
  in CI.
- `docs/tasks/2-fix-all-test-failures.md` advises `-p no:randomly`, but
  `pytest-randomly` is not in `pyproject.toml` or `uv.lock`.
- CI runs `uv run --with "playwright==1.61.0" pytest`; `server/README.md`
  says that form breaks. One of them is wrong.
- `conftest.py` mutates the module global `ROOT`; the suite cannot run in
  parallel.

### 14. Tooling and CI (Strong)

`pyproject.toml` has a `[tool.ruff.lint]` section. Ruff is not a dependency
and CI never runs it. `ruff check` reports 58 errors (54 auto-fixable) and
`ruff format --check` reports 10 files. There is no mypy, no pre-commit, no
JavaScript formatter or linter, and no lint job. The only gate is the test
suite, and it is red.

### 15. Documentation (Strong)

There are 10 502 lines of Markdown for 4 313 lines of Python and about
2 700 lines of JavaScript. The goal is fewer lines of prose than code.

- **Stale.** `server/README.md` lists `/f/` URLs as a feature, counts 56
  browser tests (there are 75), and says the suite passes.
  `server/CONTRIBUTING.md` states HTMX invariants and calls the cutover
  unfinished. `server/TASKS.md` marks `/f/` as in progress and numbers two
  issues #46 and #47 twice, in conflict with `ISSUES.md`. Root `TASKS.md`
  marks "editing starts with the cursor at the top" as completed, and the
  check fails.
- **Duplicated.** Three issue trackers exist: root `TASKS.md`,
  `server/TASKS.md`, `server/ISSUES.md`, plus `static/TASKS.md`. The
  two-edition architecture is explained at length in root `README.md`,
  `server/README.md`, `server/CONTRIBUTING.md` and `static/AGENTS.md`.
- **History in the working tree.** `server/lmt/` is 4 360 lines of literate
  reconstruction with no tangler in the repository to check it.
  `server/PLAN-18.md`, `PLAN-19.md` and `PLAN-20-shared-frontend.md` are
  3 217 lines that call themselves history.
- **Scratch committed.** `server/.pi/settings.json` contains `{}`.
  `server/mobile-narrow-preview.png` sits beside `pyproject.toml`.
  `architecture-review-20260904.html` sits at the root and nothing links to it.
- **Missing.** `README.md` says MIT and there is no `LICENSE` file. There is
  no `CHANGELOG.md`, `SECURITY.md` or root `CONTRIBUTING.md`.
- **Not in Simplified Technical English.** No existing document is. This
  review and its two companions are the first. The rest are scheduled in
  `docs/ROADMAP.md`.

### 16. Dead code (Strong)

`static/hotreload.py:30` points at `static/src/`, which does not exist.
`forgetRoots` (`storage.js:75`) has no caller. `vfs.is_vfs_file` is called
only from dead code. See also findings 2 and 10.

## Review of the previous review

The review of 2026-09-04 proposed four candidates.

| Candidate | Verdict then | Verdict now |
| --- | --- | --- |
| 1. Decide the file kind once | Strong | Correct and still open (`docs/tasks/6-*.md`) |
| 2. One rule for entry order | Strong | Correct and still open (`docs/tasks/7-*.md`) |
| 3. Consolidate the two finders | Worth exploring | Decided in code by `0cae978` one day later, without a written decision and without deletion. This is the cause of finding 1 |
| 4. `ViewSpec` for the VFS | Speculative | Correctly gated; unchanged |

**What it got right.** Candidates 1 and 2 are exact. The reasoning about
deep modules and seams is sound. It said clearly that candidate 3 needed a
decision, not a report.

**What it missed.** It was scoped to hot spots from commit history and said
so. Inside that scope it did not see six things:

- the absence of a module system (finding 4),
- the preview rebuild on every render (finding 6),
- the absent lint gate (finding 14),
- the volume and staleness of documents (finding 15),
- the security notes (finding 12),
- the two test harnesses (finding 13).

It did not run the static suite.

**What went wrong after it.** The report ends with "Which of these would you
like to explore?". The next commit answered by disabling routes. No ADR, no
deletion, no test update. The lesson for the roadmap has two parts. A
decision that changes behaviour is written down the day it is made. The code
that it retires is deleted in the same change.

## Honest summary

Filemill is a small project with an unusually clear design and unusually
good explanations. The three ports are real. The measurements behind the
decisions are real. Most projects never get this far.

Today it is also in a half-migrated state. Both test suites are red. There
is no lint gate. There is more prose than code, and much of the prose
describes code that no longer exists. The core cannot be loaded without one
HTML file's script order, which blocks the native shells the goals ask for.

None of this is hard to fix. All of it is discipline. `docs/ROADMAP.md`
gives the order.
