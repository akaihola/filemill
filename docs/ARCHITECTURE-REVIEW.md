# Architecture review and remediation plan

Checked against commit `1cb03863` on 2026-09-25; before [96]'s history rewrite
it was `6ca2580`. This document replaces the
reviews of 2026-09-05 and 2026-09-19. It keeps only the findings that the
current code still shows, merges the findings the two reviews shared, and gives
one remediation order. `docs/GOALS.md` states the target. `TASKS.md` records
status.

## How to read this review

- **Severity.** P1: fix before relying on the build for ordinary writable use or
  wider exposure. P2: the next correctness and reliability work. P3: cleanups
  and audits.
- **Evidence.** Paths are relative to `server/src/filemill/` unless they start
  with `static/`, `docs/`, `.github/`, `server/` or `native/`, which are
  repository paths; `static/` means the repository's top-level `static/`. `ui/` is the symlinked shared frontend. Line numbers are
  for the commit above.
- **Verification.** This consolidation re-read the cited code. It did not rerun
  the browser reproductions of 2026-09-19. A finding that was a structural risk
  there stays a risk here.
- **Issues.** `[N]` is issue N in `TASKS.md`, described in `docs/tasks/N-*.md`.
- **Numbering.** A1–A12 replace the numbers 1–16 of 2026-09-05 and F1–F13 of
  2026-09-19. Completed task descriptions that cite the old numbers are history.

## Architecture as it is

- **Two editions, one frontend.** The static edition starts at
  `static/index-dev.html` → `ui/entry-static.js` → `ui/adapters/app-fsa.js`.
  `static/build-index.py` concatenates the ES module graph into the committed
  `static/index.html`. The server edition starts at `cli.py` → Uvicorn →
  Starlette in `app.py`, which serves the same `ui/` with an import map and
  answers `/api/*`, `/w/` mounts and root-relative resource URLs. A Linux
  WebKitGTK shell (`native/webview/` → `ui/entry-native.js`, issue [30])
  supplies the three ports natively and passes the main UI scenario
  ([ADR 0079], 2026-10-17).
- **One URL per file.** `urls.py` parses `?filemill=raw|render|highlight`
  and `?layout=full-columns|compressed-columns` ([ADR 0067]). `raw`, the
  default, serves the bytes; every other view serves the shared shell.
- **Three ports.** `ui/core/ports.js` declares `FS`, `PREVIEW` and `ROUTER`,
  including `FS.node`, `FS.blob`, optional `FS.write`, `FS.remove` and
  `ROUTER.write(state, replace)`. Each edition supplies adapters.
- **A DOM-free model.** `ui/core/model/` holds state, selection, sort, folding,
  keyboard mapping, deep links, JSON folds, Markdown task toggles and the
  previews' safe-URL rule ([ADR 0082]), tested by `ui/core/model/test.mjs`. The
  rest of `ui/core/` is a DOM-coupled singleton.
- **One fold dial with stops.** Horizontal scroll is a dial, not a translation
  ([ADR 0021]). The scrollbar spans one stop each way and is re-based once a
  scroll settles, so a fling lands on the next stop; left of natural the
  leftmost columns widen to fill the finder ([ADR 0075], [81], 2026-10-11).
  `ui/core/model/folding.js` holds the arithmetic; `ui/core/layout.js` owns
  the scroll range and is the only writer of the dial. Resizing remaps widened
  positions when the available stops change, preserving the visible column count
  where possible and clamping partial positions to the new range. The rail span
  uses the adjusted base so fractional stops remain native scroll endpoints
  ([81] review fixes, 2026-10-11). A sideways wheel over
  the preview turns the dial until its end, where the preview is as wide as
  the screen allows; only then do the preview's own scrollers, a wide code
  block among them, take the gesture ([ADR 0076], [78], 2026-10-11).
  Native fullscreen and its layout fallback give the preview the gesture
  immediately, before the wheel latch is checked, because the preview already
  fills the screen ([78] independent-review fix, 2026-10-11).
  A wheel gesture keeps the axis it took in its first 6 px. Sideways drift
  in a vertical swipe does not turn the dial. While the dial takes a sideways
  swipe, its vertical drift does not scroll the document ([ADR 0084], [110],
  2026-10-19).
  A glide waiting for its frame starts only if no later dial write replaced
  it. A layout that finds the dial already at its resting place stops a glide
  still heading elsewhere ([ADR 0022], [113], 2026-10-20).
  A new root resets the dial through the layout module. The reset cancels
  the old glide and clears its settle timer, so the first layout establishes
  the new scrollbar range at once ([94], [ADR 0086], 2026-10-19).
  These fixes keep a mount during a refresh's glide from folding the focused
  root. General navigation cancellation remains A9. The history reconciliation
  on 2026-10-20 retains both fixes and assigns the reset decision [ADR 0086];
  [ADR 0084] keeps the wheel-axis decision. The reset also clears the old
  wheel gesture, whose axis would otherwise survive its cancelled timer.
- **Virtual filesystems.** JSON, JSONL and CSV are browser adapters
  (`ui/adapters/vfs-json.js`, `vfs-csv.js`). Markdown and reStructuredText
  browse by their headings the same way (`vfs-doc.js`, outline in
  `ui/core/model/headings.js`, [ADR 0070]). SQLite, archives
  (tar, compressed tar and zip, [ADR 0072]) and Git bundles (through `git`,
  [ADR 0073]) are server providers registered in `vfs.py`. The WebVTT provider
  registered there lists no entries; the browser renders transcripts. An archive member
  or a bundle blob has bytes of its own, so `vfs.py` has a second protocol,
  `VFSMemberProvider`, and `/api/preview` and `/api/raw` take the member's
  virtual path as `v`. `HTTP.blob` sends it too, so a JSON or JSONL member
  browses in the browser like the same file on disk ([84], 2026-10-11).
  Declined JSON/JSONL entries become leaves, cached rows lose their chevrons,
  and the navigator closes any loading column opened before the decline. Size
  and JSONL read/parse failures stay visible in the preview ([84] review
  follow-up, 2026-10-11).
  A member that the server renders (an image) reuses the browser's own
  markup, `img.pv-img`, so one stylesheet scales both ([85], 2026-10-11).
  A Markdown, `.docx` or `.pptx` member renders in the browser like the same
  file on disk, and a Markdown member opens by its headings ([86],
  2026-10-11); a reStructuredText member stays with the server renderer.
  Markdown links resolve from the member's directory, including in section
  previews. Filename-like JSON keys and CSV labels remain data values and
  records, without document heading columns ([86] review fixes, 2026-10-11).
  Left-arrow navigation reselects a document or parent section through the
  shared navigator, restoring its full preview and URL while removing deeper
  section selections ([80], 2026-10-11). Automatic README/index selection
  applies only to ordinary folders, so headings with those names do not replace
  the selected document or parent section ([80] review correction, 2026-10-11).
  Document sections show their heading text without a row icon. Their previews
  omit the file summary heading and divider, leaving the document's own heading
  at the top of the content ([79], 2026-10-11).
  Section resource URLs have fresh-load HTTP and browser coverage ([112],
  [ADR 0085], 2026-10-19). The existing `api.split_vfs` route accepts document sections;
  heading existence stays with the browser. A missing section at any depth
  restores the whole document in the DOM-free deep-link model.
  Markdown previews preserve their
  renderer IDs and add GitHub fragment aliases. The path router supplies the
  fragment, and the DOM renderer scrolls the preview body after fonts are ready.
  Fragment browser checks cover Chromium and Firefox with fresh and warm
  service-worker caches. A running server must restart after UI updates so
  its startup asset-version map matches the served files ([112] follow-up,
  2026-10-19).
- **Persistence.** Files are the only durable data. The browser keeps recent
  folder handles in IndexedDB, settings in localStorage, navigation in history
  and application assets in Cache Storage.

### What is healthy

Keep these.

- The three ports and the shared frontend. There is one copy of `ui/`.
- Decisions are recorded with their measurements in `docs/adr/`.
- The quality gate runs. CI runs `deno fmt --check`, `deno lint`, the model
  tests, `build-index.py --check`, both static suites (bundle and `--dev`) and
  the server suite with coverage (`.github/workflows/publish.yml`), each with
  `--durations=20`. [CONTRIBUTING.md](../CONTRIBUTING.md#tests) describes the
  lint job, the three parallel browser suites and the publish gate ([90],
  2026-10-14). A new run cancels only
  older runs of the same workflow and ref, so pull requests cannot cancel main;
  only main publishes. The actions use Node.js 24, including the nested Pages
  artifact uploader; setup-uv retains cache pruning explicitly ([94],
  2026-10-17). [Main run 39318918168](https://github.com/akaihola/filemill/actions/runs/39318918168)
  passed lint, 157 bundle tests, 157 development tests, 939 server tests and
  Pages deployment without Node.js 20 annotations ([93]/[94], 2026-10-19).
  All six served assets match commit `7da2e69`.
  The preview threshold browser regression waits for
  the expected fold count before measuring geometry, since navigation state can
  precede a deferred scroll write even with CSS scrolling set to `auto`
  ([93], 2026-10-17). Issue [106] adds the `noqa` issue-link guard that
  CONTRIBUTING.md describes to the pre-commit gate (2026-10-19). Its six
  suppression sites now use equivalent unsuppressed code. Provider
  imports still register in the same order. The disabled Python/LibreOffice
  PPTX tests and unused helper are removed; browser PPTX checks remain.
  The baseline and
  dispositions are in `docs/testing/remaining-red-tests.md`. Browser checks in
  the static pytest suite and server tests wait for observable state, including
  scroll/dial stability and completed storage writes, rather than fixed sleeps.
  A source guard prevents fixed browser waits from returning (2026-10-17).
  The keyboard browser suite writes server logs to a temporary file. An unread
  subprocess pipe could fill under concurrent load and block directory responses.
  A small-pipe regression covers that failure. The mobile tap helper sends
  actual touch input. The landscape regression checks paired press/release row targets:
  native scroll-into-view can turn the fold dial and move a mouse-click target
  between press and release. Existing geometry checks remain unchanged; the
  shared UI is unchanged ([98], 2026-10-17).
- Static browser checks run as separate pytest tests under `static/tests/`;
  the README's [Tests](../README.md#tests) section lists the commands and
  fixtures ([25], 2026-10-17). The fixed-wait guard scans the moved tests recursively. Copy tests install
  and pause their clock in one operation, so setup cannot pause in the past.
  The fold-animation test waits for its navigation setup to finish before
  measuring the animation, including with slow directory responses.
  Touch checks also wait for the dial to settle before pressing a row. The
  Back/Forward regression creates one preview history entry explicitly, so a
  slower intermediate folder read cannot add an extra setup entry
  ([99], 2026-10-17).
  The horizontal keyboard test waits for preview scroll movement after each
  scroll key. It covers normal writes and writes deferred across animation
  frames, with the same navigation, focus and directional assertions
  ([108], 2026-10-19).
  The [94] follow-up also waits for scrollable preview content before sending
  the key and tests delayed file reads. Preview geometry checks wait for the
  fold count, since the native scroll position can change before the scroll
  event repaints the columns. The server ←/→ URL check waits for the render
  that opens each selection and reads `location.href`, because `page.url` can
  trail in-page history writes ([113], 2026-10-20).
- Real filesystem tests without a picker: `static/tests/test_url.py` drives the real
  FSA adapter against the origin private file system.
- In the browser, size limits and the image extension list have one home,
  `ui/core/limits.js`. The server keeps its own: `IMAGE_EXTENSIONS` in
  `vfs.py`, without `avif`, `bmp` and `ico`, and the 512 KiB
  `SYNTAX_SIZE_LIMIT` in `preview.py` (A12, corrected 2026-10-19 by [109]).
  JSON documents use a separate 8 MiB limit, with a metadata check before
  fetching and a blob check before parsing ([ADR 0071], 2026-10-07).
- The server binds to `127.0.0.1` by default (`cli.py:21`).
- A public instance (`--public` or `FILEMILL_PUBLIC`) never lists or serves a
  path with a component that starts with `.`, nor follows a symlink into one
  ([128], [ADR 0087], 2026-10-20). `paths.py` holds the rule beside
  `resolve_safe`, which takes `public=`; `app.py` checks each request path
  before resolution and filters listings and search results.

### Rules for changes

- A decision that changes behaviour gets an ADR in the same change.
- Code that a change retires is deleted in the same change.
- Keep the shared UI and the concatenating builder. Do not add a framework,
  bundler, ORM or general `ViewSpec` without a failing, measured case.
- Keep native work ([29] → [30] → [31], [ADR 0066]) behind a stable browser
  preview lifecycle (A9). Status 2026-10-19: [29]–[31] are complete with A9
  still open; A9 below records the native cost.

## Findings

| ID  | P  | Finding                                                   | Effort / risk | Depends on |
| --- | -- | --------------------------------------------------------- | ------------- | ---------- |
| A1  | P1 | Resolved 2026-10-19: index containment [103]               | S / low       | —          |
| A2  | P1 | Resolved 2026-10-19: inert previews [104]                  | M / medium    | with A3    |
| A3  | P1 | Resolved 2026-10-19: mutation policy [103]                 | M / medium    | —          |
| A4  | P1 | Saves are neither atomic nor conflict-checked             | M / medium    | A1, A3     |
| A5  | P1 | Service workers cache file bytes and break offline misses | M / medium    | —          |
| A6  | P2 | Virtual-path round trip is unverified                     | S / low       | —          |
| A7  | P2 | SQLite labels double as identities; errors look empty     | M / medium    | A6         |
| A8  | P2 | Preview routing and representation disagree across modes  | M / medium    | A2         |
| A9  | P2 | The preview is rebuilt on every render                    | M / medium    | A8         |
| A10 | P2 | Limits bound the result, not the work                     | M / medium    | A4, A6, A8 |
| A11 | P2 | Current documents contradict the code                     | M / low       | each fix   |
| A12 | P3 | Smaller defects and audits                                | S each / low  | —          |

Effort: S is up to a day, M one to three days.

### A1. The directory index escapes the root check

Resolved 2026-10-19 ([103], [ADR 0081]). The final index file is resolved with
the request zones before serving. The resource/raw/index/mount symlink matrix
covers in-root files, nested escapes and direct-root bookmarks. Other derived
file responses were audited; see the ADR. The evidence below describes the
earlier code.

`app.py:405-407` (`resource`) validates the requested directory, then sends
`target / "index.html"` through `FileResponse` without resolving it. On
2026-09-19 a nested `sub/index.html` symlink to a file outside the root returned
404 at `/sub/index.html` but 200 with the outside bytes at `/sub/`.

**Acceptance.** An escaping nested index returns the same denial as its explicit
URL. In-root indexes and deliberate direct-root bookmark symlinks keep working.
Other derived-file responses are audited the same way.

### A2. Preview content can execute as Filemill

- The wikilink rule in `ui/adapters/preview-rich.js:187-202` turns a whole
  markdown-it text token into `html_inline` and escapes only the link target and
  label. Other text in that token becomes raw HTML, despite `html: false`. On
  2026-09-19 an image event handler beside `[[note]]` ran in the app page.
- `docxHTML` (`preview-rich.js:341`) inserts converter HTML without a sanitizer.
  This is an audit target, not a reproduced exploit.
- Every entry module calls `exposeCore()` (`ui/core/debug.js`), so any script
  that runs in the page shares FS and state.
- Resolved: the HTML preview iframe now has `sandbox=""`
  (`ui/core/renderers.js:171`). The server's iframe for an archive's HTML
  member had none until [114] (2026-10-20), so its script ran as Filemill.
  The PDF iframes stay unsandboxed in both renderers; the raw route serves a
  `.pdf` member as `application/pdf`.

**Acceptance.** Crafted Markdown stays inert with and without wikilinks, and
malformed wikilinks are escaped. Links, code and footnotes still render. Unsafe
URLs in DOCX output and `.desktop` links do not execute. Bare-HTML web serving
at the server root keeps working and its trust boundary is documented in
`SECURITY.md`.

Resolved 2026-10-19 ([104], [ADR 0082]):

- A wikilink is now markdown-it link tokens, and the text beside it stays an
  escaped text token. Malformed wikilinks stay text.
- Preview link targets pass one safe-protocol rule, `ui/core/model/safe-url.js`
  with a copy in `preview.py`: `http:`, `https:`, `mailto:` or scheme-less.
  `.docx` output keeps only mammoth's tags and attributes. Browser-rendered
  reStructuredText and `.docx` lose event handlers and unsafe `href` and `src`
  values. Server-rendered reStructuredText loses unsafe `href` and `src`
  values. Both `.desktop` renderers show an unsafe URL as text.
- Markdown comment rules hide inline and block comments without enabling raw
  HTML ([111], [ADR 0083], 2026-10-19). Code, Source and Raw retain comment
  text. Source line numbers still identify task checkboxes.
- The same audit found that docutils writes `javascript:` link targets as
  given. Both reStructuredText renderers now apply the rule.
- `SECURITY.md` names the bare-HTML trust boundary, and
  `server/tests/test_resource_routes.py` keeps that serving working.
- Tests: `static/tests/test_rich.py` (crafted Markdown with and without a
  wikilink, `.docx`, `.desktop` and browser reStructuredText links),
  `server/tests/test_preview.py` (server reStructuredText and `.desktop`) and
  `ui/core/model/test.mjs` (the rule's edge cases).
- Unchanged: `exposeCore()` still shares FS and state with any script in the
  app page. A bare HTML page at the root already has the same origin, so it
  gains nothing from it.

### A3. Save and delete accept unrelated origins

Resolved 2026-10-19 ([103], [ADR 0081]). Both routes check Origin, Host and a
per-process mutation token before path resolution or body consumption. The HTTP
adapter sends the shell token. Two-origin browser tests cover local and
configured reverse-proxy writes. Same-origin hostile HTML remains trusted
content and A2 remains open; [104] resolved A2 later on 2026-10-19. The
following evidence describes the earlier code.

`POST /api/save` and `DELETE /api/delete` (`app.py:306-323`) have no Origin,
Host or token check. On 2026-09-19 a `text/plain` POST with an unrelated Origin
overwrote a file and returned 200. Sending no CORS headers stops reads, not
writes. Any `.html` served same-origin from the root can also call these
endpoints. `SECURITY.md` and `CHANGELOG.md` describe the CORS removal as if it
restricted access.

**Acceptance.** An unrelated-origin POST cannot change a fixture file. A delete
without valid authorization fails. The shipped UI still saves and deletes
through configured local and reverse-proxy origins. Checks run before the body
is read. UI and server change together; `SECURITY.md` names the policy.

### A4. Saves are neither atomic nor conflict-checked

`api.py:303-320` (`save_file`) calls `target.write_bytes(data)`. A failed write
leaves a truncated file. Reads and writes carry no revision, so a second tab or
an external editor is overwritten silently. `api_save` buffers the whole body
before the size check and runs blocking I/O on the event loop. FSA writes have
no external-change check and no abort on failure. Navigation deliberately
discards unsaved edits ([28]); that is not in scope.

**Acceptance.** A simulated write failure leaves the old bytes intact. A stale
save is rejected with a conflict and the draft stays visible. Symlink and
permission behaviour of the replacement is defined and tested.

### A5. Service workers cache file bytes and break offline misses

In `static/sw.js`, every same-origin GET outside `/api/` is answered from the
cache first, navigations included. `server/src/filemill/static/sw.js` sends
navigations to the network, with an inline recovery page when that fails, and
answers every other same-origin GET from the cache first (corrected
2026-10-19, [109]). So root-relative files and `/w/` bytes that a page embeds
are cached, including `no-store` responses (server `:90`, static `:70`). A cached
response wins over the fresh one, so the first read after a save can be stale.
`cached || networkFetch || new Response(...)` (server `:96`, static `:76`) tests
the promise, so an offline miss resolves to `null`. Activation deletes every
cache name except `filemill-v1`, including other applications' caches on the
same origin. Root precaching can capture a user's `index.html`. [ADR 0063]
promises a recovery page that uncached navigation cannot reach.

**Acceptance.** Viewing a file adds no document bytes to Cache Storage.
Unrelated caches survive activation. A cold offline navigation gets a valid
recovery response. An upgrade purges legacy `filemill-v1` entries without
clearing remembered folder handles.

### A6. Virtual-path round trip is unverified

Paging and unevicted rows are resolved ([ADR 0068]). One part of the earlier
listing finding was not verified by that change: paths with `%`, `/` in virtual
keys, Unicode and empty keys must round-trip through a deep link.

**Acceptance.** Each of those paths reloads and restores its selection.
Related: [7], [22], [39], [45], [61].

### A7. SQLite labels double as identities; errors look empty

`providers/sqlite.py` builds names with `_truncate` (`:118`, `:148`), and
`_row_key` truncates keys, so two rows whose keys share a long prefix get the
same name and path. `SELECT rowid` (`:139`) fails on WITHOUT ROWID tables, and
`list_entries` catches every exception and returns `[]` (`:51`), so the table
looks empty. `_row_key` runs schema queries once per row.

**Acceptance.** Long colliding keys stay separately selectable and reloadable.
WITHOUT ROWID tables are readable or report "unsupported". Corrupt databases
show an error. Schema facts are read once per listing. Connections stay
read-only. No ORM. Related: [34], [61].

### A8. Preview routing and representation disagree across modes

- `withRichPreview` (`ui/adapters/app-http.js:124-137`) sends every non-virtual
  RST node to `PreviewHTTP`. The server's local-folder mount (`:191-196`) uses
  the same wrapper, so a browser-owned RST file requests
  `/api/preview?p=undefined`. See [41].
- Resolved 2026-10-11 ([89], [ADR 0077]): view state no longer requires a
  router. Both editions use `withHighlighting` from
  `ui/adapters/preview-local.js`, so Markdown and WebVTT switch between
  rendered content and source in static and local-folder modes too. Raw uses
  optional `FS.rawURL` for served files and `FS.blob` for browser-owned files;
  core owns and revokes the latter's object URL.
- Resolved: `PreviewLocal` now applies `TEXT_MAX` only to text
  (`ui/adapters/preview-local.js:38-41`).

**Acceptance.** Local-folder RST makes no `/api/preview` request.
Source/Rendered/Raw behave the same, and as documented, in static, served,
local-folder and virtual modes. Existing issues [10], [38], [41], [42], [56] and
[63] keep their own scopes.

### A9. The preview is rebuilt on every render

`renderPreview` (`ui/core/render.js:462-471`) builds a new element and calls
`PREVIEW.revoke()` on every `render()` unless an editor is open. A resize, a
fold or a settings change therefore reads and parses the file again, and resets
scroll and media. So does ← from the preview: a scroll key pressed before the
new fill lands has nothing to scroll ([113], 2026-10-20). [21] is marked Completed but its cache is not in the source.
[29]–[31] were completed without it. `navSeq` guards `choose` and refresh
(`ui/core/nav.js:50`); `applyPath` uses a shared `applying` flag and mutates the
path across awaits. The condition-based wait audit (2026-10-17) confirmed the
race: a click on a different folder during a root refresh can leave the old
child appended to the new chain. The existing static check awaits the refresh
before clicking and now describes that scenario accurately; overlapping
navigation remains part of this finding.

Deletion now marks the target path as pending, blocks new preview fills under
that path, and waits for active fills before `FS.remove` ([97], [ADR 0078],
2026-10-17). This prevents preview and editability reads from reaching files
after removal. It includes previews of children of a deleted folder. General
preview reuse and overlapping navigation remain open.

In the native shell on 2026-10-17, one `render()`
with a 400 KB single-line JSON source selected made a new preview element and
read the file twice. WebKit then spent 1.4–2.8 s wrapping that line at each
new width, against 10–17 ms in Chromium. A resize pays this twice ([30]).

**Acceptance.** Resize and fold cause no new provider call. Save, refresh and
mode change invalidate the preview. A delayed old navigation or preview cannot
replace the current selection. Related: [39], [40], [64].

### A10. Limits bound the result, not the work

- Search (`api.py:40-95`) runs ripgrep with
  `subprocess.run(capture_output=True)` and stops parsing at 100 matches only
  after the process ends. The client abort does not stop the subprocess.
- `preview.py:read_text` and the RST path read whole files. PPTX and DOCX have
  no archive expansion limit. FSA metadata sweeps use unbounded `Promise.all`.
  Tar and zip browsing ([ADR 0072]) is bounded: `MAX_MEMBERS` on the index and
  `MEMBER_MAX` on a member read. Git bundle browsing ([ADR 0073]) is bounded:
  `BUNDLE_MAX` on the file, `MEMBER_MAX` on a blob, a timeout per `git` call.
  JSON folding is bounded by `JSON_FOLD_DEPTH` rather than the engine's stack
  ([ADR 0080], 2026-10-17).

No load benchmark exists; measure before adding pools or caches.

**Acceptance.** Byte, match and archive limits cap the work, and results say
when they are partial. Child processes are reaped on timeout or cancel.
Truncated text is never editable as if complete. Related: [49], [60].

### A11. Current documents contradict the code

- Corrected 2026-10-19 ([105]): `README.md` now records the
  [edition/renderer matrix](../README.md) and links to renderer selection,
  extraction and server implementations. Browser-owned RST routing remains A8.
- Corrected 2026-10-19 ([105]): `server/CONTRIBUTING.md` links the shared facts,
  removes current instructions for the retired upload pipeline, and describes
  CI's branch coverage measurement without claiming a 100% threshold. Its old
  local-folder measurements remain explicitly historical.
- Corrected 2026-10-19 ([105]): `static/AGENTS.md` documents FSA writes/deletes,
  permission requests, renderer downloads and document resource requests.
  Corrected 2026-10-19 ([107]): ADRs 0001, 0005 and 0034 now date the
  superseded upload-render route, lastSel storage and read-only application
  contract, with replacing code/task references and original evidence intact.
- Corrected 2026-10-19 ([107]): `docs/ROADMAP.md` is a dated
  [status index](ROADMAP.md#status-index-2026-10-19) for all ten phases, and
  [107] records dated corrections for task 2 and the completed editor-cursor
  item. GOALS acknowledges the Linux prototype without changing the native
  goal.
- Corrected 2026-10-19 ([109]): a pass over `README.md`, `SECURITY.md`, GOALS,
  the roadmap, this review, `docs/testing/`, the ADRs and the docstrings of the
  modules they describe fixed the statements the code contradicts. ADRs that
  later code or ADRs replaced now say so. The issue lists the open questions.
- Corrected 2026-10-19 ([105]): `server/README.md` distinguishes CLI root,
  bind and live options from direct ASGI environment lookup, citing `cli.py`,
  `app.py` and `env.py`. Service-starting examples were verified against code
  without starting or restarting a service.
- The CORS and write-authority descriptions in `SECURITY.md` and `CHANGELOG.md`
  were corrected with [103] on 2026-10-19. Caching remediation remains A5.
- Status correction 2026-10-19 ([107]): the default-bind item is already
  under Completed / Accepted, unchecked. `cli.py` defaults to `127.0.0.1`.
  No acceptance or other issue state changes are part of these corrections.

The [105] documentation corrections leave A2, A4 and A5 open; A1/A3
are resolved by [103]. No renderer or security behavior changed. [104]
resolved A2 later on 2026-10-19.

Remaining after [109], 2026-10-19: A4/A5 and A6–A10 remain open, including
browser-owned RST routing and preview reuse. The
[roadmap status index](ROADMAP.md#status-index-2026-10-19) records the open
roadmap work, policy decisions and CI proof. These documentation patches
resolve no security behavior.

**Acceptance.** Each fix corrects its documents. A final pass checks every
advertised command in a clean environment. [107] dates the three named
superseded ADRs; it does not establish that final command audit.

Resolved 2026-10-11 ([82]): the Playwright run commands in `README.md`,
`server/CONTRIBUTING.md`, `static/AGENTS.md`, `static/FSA-TEST-CHECKLIST.md`
and the static scripts no longer name a version; they use the locked server
project. `ui/adapters/README.md` lists the renderers
`app-http.js` registers. `server/tests/test_docs.py` keeps both true. The
2026-10-11 independent-review follow-up also checks prose version declarations
against the pin, preserves recorded-failure exemptions, and verifies that the
server test command runs from `server/`.

Documentation portability pass, 2026-10-17: development instructions use
portable fixture roots and conditional browser setup. Historical task examples
use generic hosts and paths while retaining dates, measurements and commit
citations. `server/tests/test_docs.py` checks for known private setup references.
This documentation change does not alter application behavior or the remediation
order above.

### A12. Smaller defects and audits

- Resolved 2026-09-26: `rt` in `app.py:46` called `int()` on query values, so
  `page=bad` was a 500. `30cbef21` ([ADR 0068]) removed the only `int`
  parameter, `page`; `page=bad` is now ignored. The `int()` branch stays,
  unused.
- `kvPut` (`ui/adapters/storage.js:45-46`) is not awaited to transaction
  completion, and `rememberRoot` read-modify-writes across awaits. Multi-tab
  updates can be lost.
- `vfs.is_vfs_file` (`vfs.py:105`) has no caller in `server/src`. Providers
  register as an import side effect (`vfs.py:111-116`), and the order matters.
  Resolved, 2026-10-07: browser-owned JSON paths use the same safe real-file
  resolution and client validation as JSONL paths ([ADR 0071]).
- `<div class="preview-error">` is built by hand in seven places across the
  server.
- The server shells out: ripgrep for search, `git` for bundles. Neither
  absence is reported at start-up. `providers/gitbundle.py` looks `git` up
  once at import and, without it, leaves bundles plain files; search fails per
  request.
- Core knows the server: `ui/core/search.js:35` builds `/api/search` URLs. VTT
  parsing and file classification exist in both Python and JavaScript.
- Rows are clickable `div`s without full list semantics. No assistive technology
  audit has been done.

## Resolved since the earlier reviews

Do not reopen these without new evidence.

| Earlier finding                                                                                       | State now                                                                       |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Red test suites, false-green static scripts, no lint gate (2026-09-05 #1, #13, #14; F4)               | CI and pre-commit run real gates; see [remaining red tests]                     |
| Half-deleted HTMX finder (#2)                                                                         | Routes, handlers, `columns.py` and HTMX tests removed                           |
| JSON key order (#3)                                                                                   | `node.ordered` is honoured by `visibleKids`                                     |
| No module system (#4)                                                                                 | ES modules with an import map; the builder concatenates them                    |
| Duplicated limits and image lists (#7)                                                                | `ui/core/limits.js`                                                             |
| No media queries (#8)                                                                                 | Portrait and landscape phone rules in `ui/core/styles.css`                      |
| Delete fails in FSA and after success (F7)                                                            | `FSA.remove` uses `node.parent`; `deleteEntry` no longer calls `actions.render` |
| Unsandboxed HTML preview (F2, part)                                                                   | `sandbox=""`, for archive members too since [114]                               |
| Images over 512 KiB rejected (F10, part)                                                              | Text-only limit                                                                 |
| Descending name sort ignored                                                                          | `visibleKids` reverses when `desc`                                              |
| ↑/↓ over folders stacked one entry per row; Alt+arrows swallowed ([39])                               | `state.stepping` rewrites ([ADR 0050]); `keyAction` ignores modified keys       |
| `0.0.0.0` bind and `/w/` CORS `*` (#12)                                                               | Loopback default; no CORS headers                                               |
| Missing `LICENSE`, `SECURITY.md`, `CHANGELOG.md`, `CONTRIBUTING.md`; history files in `server/` (#15) | Present; history files removed                                                  |
| `static/hotreload.py`, `forgetRoots` (#16)                                                            | Removed                                                                         |
| Listing paged at 500 entries; virtual rows never evicted (A6, part)                                   | Whole listing, one scrollbar, rows evicted on scroll ([ADR 0068])               |
| Status strip items shrank and wrapped into its clipped height ([88])                                  | Only hints wrap into hidden rows, dropping from the end. Path, active messages and fold count stay visible; long text ellipsises ([ADR 0074], review correction 2026-10-11) |

## Remediation order

Each step is one reviewable change with its own regression tests and document
updates. Security steps can start at once. Never weaken a gate to pass it.

1. **Close the path escape and authorize mutations** (A1, A3). Resolved
   2026-10-19 in [103], [ADR 0081]. Validate the
   final index file with the request's zones. Add an Origin/Host check and a
   per-instance mutation token, validated before the body is read, with
   configured origins for reverse proxies. Tests: symlink matrix over resource,
   raw, index and mount routes; two-origin browser requests.
2. **Make preview content inert** (A2). Done 2026-10-19 ([104], [ADR 0082]).
   Rewrite wikilinks as link tokens or escape all untouched text. Sanitize
   DOCX output and URL-bearing fields with an explicit safe-protocol list. Do
   not add a security framework.
3. **Make saves atomic and conflict-checked** (A4). Write to a temporary file in
   the same directory and replace. Carry a revision from read to save; reject
   stale writes. For FSA, recheck before writing and abort on failure. Document
   effects on hard links and ownership. Update [28].
4. **Restrict the service workers to application assets** (A5). Network-only for
   documents, raw files and mounts. Precache a known shell route. Await the
   network failure before choosing a recovery response. Version the cache name
   and delete only this app's old caches. Test an installed upgrade. Update
   [ADR 0063].
5. **Pin the virtual-path round trip** (A6). The whole directory is listed and
   scrolled with evicting virtualisation ([ADR 0068]). Use one
   entry-construction path; keep state changes in the navigator.
6. **Separate SQLite identity from display text** (A7). Use step 5's address
   contract. Keep truncation presentational; support or reject WITHOUT ROWID
   explicitly; distinguish empty, inaccessible and corrupt.
7. **Unify preview capability and representation** (A8). Give the registry an
   explicit source and representation contract; browser-owned RST uses the
   browser renderer; Raw becomes an adapter capability.
8. **Restore preview identity and one owner for async navigation** (A9). Reuse
   the preview element per node, revision, representation and settings. Share
   one generation check across `choose`, `applyPath`, refresh and remount; each
   preview owns and revokes its object URLs. Restore [21]'s acceptance criteria.
9. **Bound work where it is acquired** (A10). Stream ripgrep with a byte and
   match budget and kill it on budget, deadline or cancel. Bound body, file and
   archive reads. Measure before adding concurrency limits.
10. **Close the documentation loop** (A11). Most corrections ship with steps
    1–9. The last pass fixes the rest, dates superseded ADRs, turns
    `docs/ROADMAP.md` into a status index, and smoke-tests every advertised
    command.

A12 items can land at any time, each with a focused test.

[ADR 0005]: adr/0005-node-lastsel-per-directory.md
[ADR 0021]: adr/0021-horizontal-scroll-fold-dial-not-translation.md
[ADR 0022]: adr/0022-the-dial-s-resting-place-never-folds-the-focused-column-nor-anything-r.md
[ADR 0034]: adr/0034-read-only-mode-read.md
[ADR 0050]: adr/0050-history-pushes-on-entering-a-column-rewrites-otherwise.md
[ADR 0063]: adr/0063-installed-pwa-server-recovery.md
[ADR 0066]: adr/0066-native-toolkits.md
[ADR 0067]: adr/0067-drop-no-columns-layout.md
[ADR 0068]: adr/0068-scroll-whole-directory-listings.md
[ADR 0070]: adr/0070-documents-browse-by-headings.md
[ADR 0071]: adr/0071-bounded-json-documents.md
[ADR 0072]: adr/0072-archives-browse-by-their-members.md
[ADR 0073]: adr/0073-git-bundles-browse-by-refs-and-trees.md
[ADR 0074]: adr/0074-status-strip-drops-whole-hints.md
[ADR 0075]: adr/0075-the-scrollbar-spans-one-stop-each-way.md
[ADR 0076]: adr/0076-a-sideways-wheel-over-the-preview-turns-the-dial-first.md
[ADR 0077]: adr/0077-preview-views-and-raw-links-work-without-routing.md
[ADR 0078]: adr/0078-delete-waits-for-active-preview-reads.md
[ADR 0079]: adr/0079-native-shell.md
[ADR 0080]: adr/0080-json-past-a-fold-depth-limit-is-source.md
[remaining red tests]: testing/remaining-red-tests.md

[ADR 0081]: adr/0081-authorize-server-mutations.md
[ADR 0082]: adr/0082-previews-link-only-to-safe-protocols.md

[ADR 0083]: adr/0083-hide-markdown-comments.md
[ADR 0084]: adr/0084-a-wheel-gesture-keeps-the-axis-it-started-on.md

[ADR 0085]: adr/0085-markdown-heading-fragments-scroll-the-preview.md
[ADR 0086]: adr/0086-new-fold-moves-cancel-older-glides.md
[ADR 0087]: adr/0087-a-public-instance-never-lists-or-serves-hidden-paths.md
