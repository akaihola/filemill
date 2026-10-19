# Check filemill's docs and ADR statuses against the code, and fix what disagrees

Steward issue, 2026-10-19 (spare quota, steward decisions D48 and D53: review
of docs, docstrings, comments and task descriptions). Goal: agentic-leverage;
filemill is tier 1 and the most active repository: 575 commits on `main`
since 2026-09-19, 150 of them in the last week. Its `docs/` holds 83 ADRs,
`ROADMAP.md`, `GOALS.md`, `ARCHITECTURE-REVIEW.md` and the testing notes.

## Work

1. Read `README.md`, `SECURITY.md`, `docs/GOALS.md`, `docs/ROADMAP.md`,
   `docs/ARCHITECTURE-REVIEW.md` and `docs/testing/` against current `main`.
   List every statement the code contradicts, every stale command, path or
   setting, and every explanation duplicated across files, with the file and
   line of both sides.
2. Go through `docs/adr/`: find ADRs whose decision the code no longer
   follows, or that a later ADR replaced, without a status that says so.
   Mark each superseded with a link to what replaced it; don't rewrite its
   reasoning.
3. Check the docstrings and comments of the modules the docs describe for
   the same contradictions.
4. Fix the text where the code is clearly right. Where it's unclear whether
   the code or the text is wrong, don't guess: list it under "Questions" in
   this issue's description.
5. Where one section repeats another, keep one explanation and link to it.

## Ground rules

- Docs, docstrings and comments only: no behaviour, test or dependency
  changes.
- No host names or private paths in any file: the docs test rejects them.

## Acceptance

- `server/tests/test_docs.py` passes.
- Every fix listed in the description cites the code line it follows.
- The description lists what changed and the open questions.

## Result, 2026-10-19

Eight read-only audits covered the files above, ADRs 0001–0029, 0030–0061
and 0062–0082, and the docstrings and comments of the described modules.
Each finding was checked against the code before a change. Code lines below
are for the commit that completes this issue. Unchanged ADRs follow the code,
or already carried a note (0001, 0005, 0021, 0034, 0065).

### What changed

`README.md`:

- Server source highlighting: Pygments colours only archive members, through
  `/api/preview` (`ui/adapters/app-http.js:143`,
  `server/src/filemill/preview.py:156`). `render_source`
  (`preview.py:129`) has no route.
- The button is "Open Folder…" (`ui/adapters/app-http.js:54`,
  `app-fsa.js:56`). Also fixed in `static/AGENTS.md`, `server/README.md`,
  GOALS and comments in `app.py`, `entry-server.js`, `app-http.js` and
  `syntax.js`.
- Pages also publishes the manifest, worker and icons
  (`.github/workflows/publish.yml:140`); same fix in `static/AGENTS.md`.
- A directory with an `index.html` serves it unless the URL has a query
  (`server/src/filemill/app.py:444`).
- No provider browses WebVTT: `VTTProvider.list_entries` returns `[]`
  (`server/src/filemill/providers/vtt_provider.py:88`).
- No `TASKS.md` item links the roadmap; roadmap issues name their phase.
- The native host opens `FILEMILL_ROOT` before the picker
  (`native/webview/main.c:239`), fixed in `native/README.md`. The README
  native section links there instead of repeating its commands.
- Duplicates cut: the second bundle/`--check` paragraph; browser install
  advice now links `server/CONTRIBUTING.md#running-tests`, as do
  `server/README.md` and `static/AGENTS.md`.

`SECURITY.md`:

- The UI no longer makes `/w/` links; `~/` resolves against `/`
  (`ui/core/markdown-links.js:8`, `1bf99afa`).
- Markdown links follow markdown-it and reject only `javascript:`,
  `vbscript:`, `file:` and `data:` (`ui/core/markdown-links.js:7`), as ADR
  0082's Consequences say. The safe-protocol list covers RST, DOCX and
  `.desktop`.
- The token paragraph now links the root-HTML section instead of repeating it.

`docs/GOALS.md`:

- `docs/tasks/3-…` was retired in `c7b7f38b`; the goal links the README.
- "The static edition sends nothing": documents can load resources, and
  renderer downloads sit behind the switch (`ui/adapters/preview-rich.js:76`).
- The decisions table is now `docs/adr/` (`static/AGENTS.md` lists links).
- Offline fallback is the `offline` entry (`preview-rich.js:417`); binary DOCX
  may have no text.
- The collator is in `ui/core/model/sort.js:3`, one per module
  (`ui/adapters/fsa.js:10`, `native.js:6`).
- Open Folder mode has no router (`ui/adapters/app-http.js:90`).
- `resolve_safe` is in `server/src/filemill/paths.py:26`; write permission is
  asked on save and delete (`ui/adapters/fsa.js:70`, `:84`).
- PPTX runs in the browser (`preview-rich.js:380`). Server-only: content
  search (`ui/core/search.js:1`), SQLite, archives and Git bundles
  (`server/src/filemill/vfs.py:142`).

`docs/ROADMAP.md`:

- The status index maps old `static/test-*.py` names in open checks to
  `static/tests/` (`587752b4`, `conftest.py:171`).
- Phase 0 records this issue's fixes to step 5's remaining server claims.
- Phase 1 links `CONTRIBUTING.md#tests` instead of repeating its gate facts.
- Phase 3: `sortKids` is in `ui/core/model/sort.js`; the `grep` needs `-r`.
- Phase 6: the removed live reload is the browser one over `/sse/reload`
  (`cb453a00`); `--live` stays (`server/src/filemill/cli.py:18`).

`docs/ARCHITECTURE-REVIEW.md`:

- Review commit `6ca2580` is `1cb03863` after [96]'s history rewrite.
- `server/` and `native/` are repository-path prefixes.
- The WebVTT provider lists no entries (`vtt_provider.py:88`).
- `ui/core/limits.js` is the browser's one home; the server keeps
  `IMAGE_EXTENSIONS` (`vfs.py:15`) and `SYNTAX_SIZE_LIMIT` (`preview.py:21`).
- [29]–[31] are complete with A9 open (`TASKS.md`).
- A5: the server worker sends navigations to the network, with a recovery
  page (`server/src/filemill/static/sw.js:74`); the static worker does not.
- A12: `page=bad` no longer 500s; `30cbef21` removed `api_dir`'s `int`
  parameter (`app.py:267`). The `int()` branch stays (`app.py:50`).
- A12: `git` is looked up at import (`providers/gitbundle.py:42`).
- Duplicates cut: the CI jobs and hooks link `CONTRIBUTING.md#tests`, the
  static fixtures link the README, A11's renderer facts link the README
  matrix, and the remaining roadmap work links the ROADMAP status index.

`docs/testing/remaining-red-tests.md` and `.tsv`:

- A dated header: 58 of the 256 node IDs no longer resolve (`587752b4`,
  `ca94b450`, `187ddc89`, `f0a2d734`, `e0349caa`, `fe9b9335`, `9cca50fb`), and
  the `server/.venv` commands predate the root workspace.
- Pre-[96] hashes now name main: `2163673` → `e142c2e4`, `055f4f6` →
  `95e7ca17`, `0cae978` → `9e931c5d` (also TSV row 12), `1257b46` →
  `9f773f0c`, `179af97` → `874faa13`, `5cfb6a8` → `fe9b9335`. `b6059f5` was
  a pre-rebase commit and is not in the repository.
- The home-link rows are superseded by `1bf99afa`; the end-user check follows
  `ui/core/markdown-links.js:8`.
- The issue moved to Completed in `59377696`, not "remains In Progress".
- The manual E2E note links `CONTRIBUTING.md#tests`.

ADRs, each with a dated note; reasoning and measurements are unchanged:

- 0002: the server imports `preview-rich.js` and renders served RST with
  docutils (`ui/adapters/app-http.js:126`, `preview.py:107`, `9fba9118`).
- 0003: `src/` is now `ui/` with `static/index-dev.html` and
  `static/build-index.py` (`d10c714e`, `e01a40b4`).
- 0025: superseded in part by 0062; `folderWidth()` replaces the clamp
  (`ui/core/dom-renderer.js:21`, `fe3a2306`).
- 0035, 0036: scope notes. The server vendors Markdown and DOCX
  (`server/src/filemill/app.py:169`, `59672dd6`), `vendored()` bypasses the
  switch (`preview-rich.js:81`), and no edition downloads a PPTX renderer
  (`90f40ed3`).
- 0037: superseded in part by 0072; archive members get Pygments source
  (`app-http.js:143`, `preview.py:156`).
- 0039: the fallback is the registry's `offline` entry (`preview-rich.js:417`,
  `ea0a3dbe`).
- 0040: no PPTX viewer pin (`preview-rich.js:380`); the server sets
  `FILEMILL_CDN` (`app.py:169`).
- 0062: extended by 0075 (`ui/core/layout.js:310`, `model/folding.js:78`).
- 0063: `uv run filemill` (`app-http.js:194`) and the worker's recovery page
  (`sw.js:74`, `87bc1f5d`).
- 0064: server RST since `9fba9118`; the focused checks are
  `static/tests/test_rich.py -k rst` (`static/tests/test_rich.py:279`).
- 0065: its `git log` needs `--full-history` to find `f73912b4`.
- 0068, twice: each names the other; `vfs-json.js` now names its file.
- 0069, 0079: the test is in `static/tests/test_ui.py` (`:835`).
- 0072: the runtime `zstandard` marker differs from the dev groups
  (`server/pyproject.toml:12`, `:51`).
- 0064, 0065, 0072, 0075 and 0076 gain missing link definitions; 0078 now
  cites [97].

Server documents:

- `server/README.md`: source is highlighted in the browser; no Mermaid exists
  in `ui/`; JSON uses the browser adapter; the worker sends navigations to the
  network (`sw.js:74`).
- `server/CONTRIBUTING.md`: adds `mutations.py` and seven unlisted test
  files; A2 is resolved ([104]); the catch-all is the resource route
  (`app.py:378`); the SSE test went with `cb453a00`; `_proxy_from_env` went
  with `6390cdc0` (`server/tests/test_browser_keyboard.py:207`).

Docstrings and comments, all without code changes:

- `api.py`: the six `/api/*` routes and `v` (`app.py:266`–`:352`),
  `paths.resolve_safe`, and metadata fetched for sorts (`ui/core/sort.js:65`).
  `urls.py` names `resolve_safe` too.
- `app.py`: `_HTML_EXTS` is unused; `ROOT` is the fallback (`cli.py:28`,
  `:32`); the resource route serves the shell (`app.py:451`); `ui_asset`;
  `.pptx` needs no module; PLAN-19 was deleted in `0454159f`.
- `env.py`: shared by `cli.py`, `app.py` and `mutations.py` (`cli.py:7`).
- `preview.py`: `render_source` has no route. `vtt_provider.py`: no entries.
- Both `sw.js` headers state the strategy the code follows (`sw.js:74`).
- `fsa.js` writes and deletes (`:70`, `:84`); `preview-local.js` names
  `PreviewHTTP` and `editableText` (`ui/editor/editor.js:26`);
  `preview-rich.js` and `app-http.js` drop the PPTX viewer; `shell.js`,
  `entry-static.js` (`:14`), `router-path.js` (`:18`, `:38`), `http.js`,
  `ports.js` (`view`, `fileKind`, `abs`, `previewFormat`: `render.js:617`,
  `http.js:35`, `renderers.js:193`), `renderers.js` (`app-native.js:39`),
  `model/folding.js` (`model/test.mjs:82`) and `ui/adapters/README.md`.
- `native/shell.nix` and `static/build-index.py` name current paths.
- `test_flings_stop_at_each_fold_stop`'s docstring swapped left and right of
  natural (ADR 0075; `ui/core/layout.js:22`).
- `static/index.html` is regenerated; only comment lines change.

Kept on purpose: the README overview beside the `ui/adapters/README.md`
module guide, the README static quick start beside `static/AGENTS.md`, the
README's ~300 µs summary beside its measurement, and GOALS one-line goals
that link to their explanation.

### Questions

1. Archive-member HTML previews are not sandboxed. `_preview_html`
   (`server/src/filemill/preview.py:237`) builds its `<iframe>` without
   `sandbox=""`, while a file on disk gets one (`ui/core/renderers.js:178`).
   An `.html` member reaches it through `/api/preview?v=`
   (`ui/adapters/app-http.js:143`). `SECURITY.md` promises the sandbox. The
   code is likely wrong; this docs-only issue leaves it. File a fix issue?
2. A5's scope. Is "the first read after a save can be stale" still true?
   `FS.blob` reads `/api/raw` (`ui/adapters/http.js:126`), which the worker
   never caches. Does ADR 0063's recovery page mean the worker's inline page,
   which any navigation reaches once the worker is installed, or the shell's
   retry? `server/README.md`'s "uncached offline navigation" sentence and
   `SECURITY.md`'s "stale cached shell" depend on the answer.
3. The server edition shows the rich-preview switch
   (`ui/adapters/preview-rich.js:116`), which changes nothing there. Hide it?
4. ADR 0048: a refused row-menu copy shows a message but selects nothing
   (`ui/core/nav.js:339`). Is that exception intended?
5. `ui/core/search.js:1` says the search control is hidden in local mode. It
   is removed only when `<html>` has no `data-root` (`:72`, `:82`), so Open
   Folder mode keeps it and searches the server root. Bug or comment?
6. The comment at `server/src/filemill/app.py:368` and
   `test_named_route_wins_over_a_directory_of_the_same_name` say a root
   folder named `api` is unreachable. Only the exact endpoint paths are
   shadowed (`app.py:506`), so `/api/note.txt` reaches the resource route.
   Reserve the prefix, or reword?
7. `/n/` (`app.py:110`) remains a second shell base beside `/`
   (`app.py:451`). Keep or drop it?
8. ROADMAP Phase 7 says "No fixed browser waits remain", but a route handler
   sleeps 0.2 s (`server/tests/test_browser_new_ui.py:2087`). Does a response
   delay count?
9. ROADMAP's rule "no skipped test without a link to an issue" meets three
   conditional skips with reasons only
   (`server/tests/test_browser_keyboard.py:997`,
   `test_browser_new_ui.py:2001`, `test_gitbundle_provider.py:11`). Narrow it?
10. GOALS says "each pin explained", but the floors in
    `server/pyproject.toml` have no comments except Playwright's.
11. GOALS' non-goal "no network use without consent" meets document images,
    which load without the switch. Goal or code?
12. ARCHITECTURE-REVIEW asks for an ADR "in the same change"; ROADMAP says
    "the same day". Which?
13. `ui/core/icons.js:2` names `build-seti-map.py`, which no commit contains.

### Follow-ups that need code changes

- `.github/workflows/publish.yml:133` says "Only the one file" above the line
  that copies five more (`:140`). A workflow-file change needs a token with
  workflow scope to push, so this issue leaves it.
- `server/src/filemill/cli.py:23`'s help says `FILEMILL_BIND` overrides
  `--bind`; it only sets the default.
- Unused code: `_HTML_EXTS` (`app.py:26`), `VIEW_LABELS` (`urls.py:49`),
  `preview_fragment` (`api.py:383`), `render_source` (`preview.py:129`),
  `VTTProvider.render_preview`, `rt`'s `int()` branch (`app.py:50`), the
  `static_fallback` band (`app.py:510`), `/sse/` in both workers, and the
  `previewFormat` reader (`renderers.js:193`). `RENDER_MAX` (`api.py:50`) now
  limits only `/api/save`, since `871a2d42` removed `/api/render`.

### Validation

- `uvx pre-commit run --all-files`: all seven hooks passed.
- `uv run pytest` on `test_docs`, `test_pwa`, `test_api`, `test_preview`,
  `test_vtt_provider`, `test_app`, `test_urls`, `test_cli`, `test_vfs`,
  `test_suppression_links`, `test_pytest_config`, `test_resource_routes`,
  `test_file_kind` and `static/tests/test_pwa.py`: 333 passed.
- `node ui/core/model/test.mjs`: passed.
- `static/build-index.py --check`: up to date; the bundle diff is comments.
- Browser suites were not rerun: no code line changed.
