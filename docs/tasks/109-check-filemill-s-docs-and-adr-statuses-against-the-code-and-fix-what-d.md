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

## Proposed answers, 2026-10-19

Prepared for [115]; checked against `cbcd8baf` on 2026-10-20. The heading
date follows the request. These are recommendations for review, not approved
decisions or implemented fixes. The original questions above remain historical.
Question 1 belongs to [114]. Each proposed change below has its own `steward`
issue in Unverified proposals; question 7 needs no change.

### Question 2 — Cache scope and offline recovery

**Recommendation — change the text; keep A5 open.** Limit the stale-read
claim to embedded resources fetched outside the API, such as document images
and `/w/` files; normal preview and editor reads use the uncached API.
Describe both recovery paths: an active server worker supplies an inline page
for failed non-API navigations, while an already loaded shell retries a failed
root mount. A first visit without a controlling worker has no such fallback.
Describe old mutation tokens as an open-page or stored-shell problem after a
restart, not proof that ordinary navigation serves a cached shell.
Draft: [117].

**Evidence.** `HTTP.blob` in `ui/adapters/http.js` reads `/api/raw`, and
`server/src/filemill/static/sw.js` bypasses API requests but caches other
same-origin non-navigation GETs; `87bc1f5d` added the navigation recovery branch
and the source checks in `server/tests/test_pwa.py`, as ADR 0063 now records.
`showServerUnavailable` in `ui/adapters/app-http.js` retries the mount, while
ADR 0081 and `test_token_changes_invalidate_existing_shells` in
`server/tests/test_mutation_policy.py` establish the separate restart-token
problem; the unresolved cache-isolation and non-navigation offline-miss defects
still justify A5.

**For Antti:** Can saved files look out of date, and can the app help when the
server is stopped — warn about stored pictures and other content inside
documents, and explain when the retry page works.

### Question 3 — A switch with no effect in the server edition

**Recommendation — change the code and its decision note.** Hide the
rich-preview download switch in the server edition, including Open Folder
mode, while its registered renderers need no third-party download. Keep the
switch where it controls downloads in the static and native editions.
Draft: [118].

**Evidence.** `59672dd6` introduced the vendored-module bypass now described
by ADRs 0035/0036 and checked by
`static/tests/test_rich.py::test_vendored_renderers` with the switch off.
`offerRichToggle` in `ui/adapters/preview-rich.js` still exposes the switch
unconditionally, although `ui/adapters/app-http.js` uses vendored Markdown
and DOCX, built-in PPTX extraction and server RST.

**For Antti:** Should the server show a preview-download switch that changes
nothing — hide it there.

### Question 4 — Clipboard refusal from a row menu

**Recommendation — change the text.** Record the intentional menu exception
in ADR 0048: a refused menu copy keeps the menu open and reports the failure,
without selecting text. Retain text selection for refused keyboard and status
path copies. Draft: [119].

**Evidence.** `45a78db0` introduced the explicit-menu distinction in
`ui/core/nav.js::copyPath`, after ADR 0048 was written.
`static/tests/test_ui.py::test_copy_menu_refusal_keeps_menu` requires an open
menu and no text selection, while `test_copy_refusal_fallback` checks selection
of the refused value for keyboard copying.

**For Antti:** If copying from a file's menu fails, should the path become
selected text — keep the menu open with an error, and keep manual text
copying as the keyboard fallback.

### Question 5 — Search after opening a local folder

**Recommendation — change the code and record the behavior.** Hide and
disable server content search while a browser-owned folder is mounted, clear
its results, and cancel pending work so late results cannot reappear.
Restore it on return to the served tree; adding local content search is
separate work. Draft: [120].

**Evidence.** `6ed49a2c` added server-only search, and
`test_content_search_opens_a_matching_file` in
`server/tests/test_browser_new_ui.py` checks served files.
`ui/core/search.js` checks `data-root` only at module load and always calls
`/api/search`, whereas `ui/adapters/app-http.js::mount` changes the filesystem
and sets the router to null without removing that attribute or disabling
search, so results concern the wrong tree and their activation expects a
router that no longer exists.

**For Antti:** Should search still look through the server's files after I
open a folder on my computer — hide it until I return to the server's folder.

### Question 6 — A folder named api

**Recommendation — change the text and strengthen the test.** Describe
collisions with exact API endpoint paths, not a reservation of the whole
prefix. Keep ordinary files under an `api` directory reachable; test both
the endpoint and a non-conflicting file. Other wildcard routes retain their
own collision rules. Draft: [121].

**Evidence.** The resource-route change `5eadcfdb` introduced the broad
comment, but the routes and `_reorder_routes` in `server/src/filemill/app.py`
give exact API endpoints priority before the resource catch-all.
`server/tests/test_resource_routes.py::test_named_route_wins_over_a_directory_of_the_same_name`
creates `api/note.txt` but requests only `/api/dir`, so its assertion does not
establish its docstring's claim that the whole directory is unreachable.

**For Antti:** Should a folder become inaccessible just because its name
matches part of an internal web address — keep ordinary files accessible and
correct the explanation.

### Question 7 — The alternate browsing address

**Recommendation — no code or text change needed.** Keep `/n/` as a supported
alternate shell base and retain root-relative file addresses as the normal
resource URLs. Removing it would break existing links and test entry points
without helping this documentation task.

**Evidence.** `5eadcfdb` added root-relative resource URLs while retaining
`UI_BASE = "/n/"`, and `ui/adapters/router-path.js` explicitly handles both
bases, consistent with ADR 0043's path-based server navigation.
`server/tests/test_pwa.py` checks the `/n/` shell, and
`server/tests/test_browser_new_ui.py` opens and navigates through it, while
`server/tests/test_resource_routes.py` covers root-relative representations.

**For Antti:** Should we remove an older browsing address that still works
and may be bookmarked — keep it.

### Question 8 — Deliberately slow test responses

**Recommendation — change the text.** Say that tests must wait for observable
state rather than pause for an assumed completion time. Allow deliberate
response delays as test input; do not claim the source guard bans every sleep
or that elapsed time alone proves a race occurred. Draft: [122].

**Evidence.** `7ddeab00` added the 0.2-second delay inside the intercepted
response in `test_declined_json_member_recovers_after_refresh` in
`server/tests/test_browser_new_ui.py`; the assertions wait for the node's
loading/error state and the resulting UI.
`server/tests/test_browser_waits.py`, introduced in `ffc5dbf4`, rejects
`wait_for_timeout`, not all sleeps, so ROADMAP Phase 7's blanket wording is
broader than the guard or the test's purpose.

**For Antti:** May a test deliberately make a file load slowly to check how
the app responds — yes, but it must judge success by what the app does.

### Question 9 — Conditional test skips

**Recommendation — change the policy text.** Require issue links for tests
disabled because of an unresolved defect or unfinished work. Allow stated
platform and optional-tool prerequisites without inventing a defect issue;
required CI prerequisites must still be installed and their checks must run.
Draft: [123].

**Evidence.** `9fa13dbe` added a Linux pipe-capacity regression whose
`skipif` excludes other platforms, while `68325e9d` added the two Git
prerequisite skips in the bundle browser and provider suites.
ADR 0073 and `server/src/filemill/providers/gitbundle.py` make Git an optional
capability, and `test_without_git_a_bundle_is_a_plain_file` describes its
fallback, so these conditions do not mean a known defect is being hidden.

**For Antti:** Should a test need a bug report when it cannot run on this
computer — no, explain the missing requirement and reserve bug links for
tests disabled by unfinished work.

### Question 10 — Reasons for dependency versions

**Recommendation — change the text and configuration comments, not the
versions.** Distinguish minimum versions, deliberate version restrictions
and the exact releases recorded in the lockfile. Explain meaningful
restrictions, including the build-backend range and Python-dependent archive
library; mark inherited minimums as unverified where history gives no reason
instead of inventing compatibility claims or pinning everything.
Draft: [124].

**Evidence.** `server/pyproject.toml` mixes unconstrained runtime dependencies,
development minimums and a Playwright release restriction, while `uv.lock`
records exact versions; `server/tests/test_docs.py` checks the Playwright
guidance, not compatibility at every declared minimum.
History identifies the Playwright browser match (`875b032b`), archive
compatibility (`b91a3d8c`, ADR 0072) and the later mypy comment (`f26da085`),
but inherited bounds from `26d515b9` and `eec53713` do not by themselves prove
that each lower limit was tested.

**For Antti:** Should we explain why particular versions of extra software
are required — yes, explain deliberate limits and be honest when an old
minimum has no verified reason.

### Question 11 — What network consent covers

**Recommendation — change the text.** Replace the blanket consent claim
with the actual boundary: the remembered switch controls third-party renderer
downloads and defaults on; it does not block document images or other
referenced resources. Preserve the no-telemetry rule and local file
processing claim, and state that external resources contact their hosts.
A general resource-permission system would need a separate product decision.
Draft: [125].

**Evidence.** GOALS introduced the broad claim in `d08f3b84`, but [109]'s
`f488ccab` corrected its privacy paragraph, README and ADR 0036 to distinguish
renderer downloads from document resource requests.
`ui/adapters/preview-rich.js` gates renderer loading, allows safe image
sources and inserts rendered document HTML, while the consent tests in
`static/tests/test_rich.py` check renderer requests rather than a general
network block; ADR 0082's safe-URL rule also permits HTTP(S) resources.

**For Antti:** Does turning off preview downloads also stop documents from
loading pictures from the internet — no, make that limit clear in the promise.

### Question 12 — When to record a decision

**Recommendation — change the text.** Use “in the same change” for decisions
that change a port or behavior, and make ROADMAP link to that rule. Preserve
the stronger contribution guidance to commit the explanation with the change.
Draft: [126].

**Evidence.** ROADMAP's “same day” rule came from `88f87563`, whereas the
consolidated architecture review `d5b0a55e` requires an ADR “in the same
change,” and CONTRIBUTING requires documentation in the same commit.
Recent behavior fixes such as `9d90ed3f` include code, tests and ADR updates
together, demonstrating the reviewable unit that the stricter wording describes.

**For Antti:** Should the reason for a behavior change arrive with the change
or later that day — include it with the change.

### Question 13 — The missing icon-map generator

**Recommendation — change the comments.** Describe the checked-in Seti map
and its recorded upstream sources in both the icon module and map header;
state that its generator is not in this repository. Keep the assets and
licence, and regenerate the static bundle if its copied comments change.
Do not invent a replacement build tool. Draft: [127].

**Evidence.** `git blame` traces the generator claim in `ui/core/icons.js`
to the UI import `69be0ef6`, but `git log --all --full-history` for
`build-seti-map.py` at any depth finds no tracked script.
`ui/vendor/seti-map.js` repeats the claim and records the Seti UI and VS Code
sources, while the existing browser icon checks and `static/build-index.py`
use the committed assets without that generator.

**For Antti:** Should we build a missing tool just because an old comment
names it — no, correct the comment to describe the icon data we actually keep.


### Validation for [115], 2026-10-20

- Baseline: `timeout 1800 uv run pytest -q tests/test_docs.py` from `server/`:
  20 passed.
- After the additions: `timeout 1800 uv run pytest -q tests/test_docs.py
  tests/test_pwa.py tests/test_resource_routes.py tests/test_mutation_policy.py
  tests/test_browser_waits.py` from `server/`: 133 passed.
- `timeout 1800 uvx pre-commit run --all-files`: all seven hooks passed.
- Temporary TestClient probes confirmed that `/api/note.txt` serves an ordinary
  file, `/api/dir` remains an endpoint, and `/n/` opens the shell even when the
  root contains an index page.
- Structure check: twelve answers, eleven `steward` drafts naming their source
  questions, and the original audit preserved byte for byte.
- No behavior changes; browser suites were not rerun. No push.

[114]: 114-sandbox-html-previews-of-archive-members-as-security-md-promises.md
[115]: 115-propose-plain-answers-to-the-docs-check-s-twelve-remaining-questions.md
[117]: 117-clarify-cache-and-recovery-claims-from-docs-question-2.md
[118]: 118-hide-the-ineffective-server-preview-switch-from-docs-question-3.md
[119]: 119-document-the-menu-copy-exception-from-docs-question-4.md
[120]: 120-disable-server-search-in-local-folders-from-docs-question-5.md
[121]: 121-clarify-api-path-collisions-from-docs-question-6.md
[122]: 122-clarify-deliberate-test-delays-from-docs-question-8.md
[123]: 123-clarify-conditional-test-skips-from-docs-question-9.md
[124]: 124-explain-dependency-constraints-from-docs-question-10.md
[125]: 125-clarify-network-consent-scope-from-docs-question-11.md
[126]: 126-align-decision-timing-rules-from-docs-question-12.md
[127]: 127-correct-icon-generator-claims-from-docs-question-13.md
