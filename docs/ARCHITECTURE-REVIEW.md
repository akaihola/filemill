# Architecture review and remediation plan

Checked against main commit `76c6142429641ea4c004645a4d3a70f6321a8d1a`
on 2026-10-20 for [the architecture re-check][132]. This replaces the
2026-09-25 snapshot at `1cb03863` and reconciles the fixes recorded since
then. [docs/GOALS.md][goals] states the target; [TASKS.md][tracker] records
work and acceptance separately.

## How to read this review

- **Severity.** P1: fix before relying on the build for ordinary writable use
  or wider exposure. P2: the next correctness and reliability work. P3:
  cleanups and audits.
- **Status.** Open: the finding still applies. Changed: part was fixed, or the
  evidence, scope or priority changed. Resolved: the cited defect was removed;
  these findings are under "Resolved since the earlier reviews". A13 and A14 are
  resolved. Resolution does not mark a task accepted.
- **Evidence.** Links are repository-relative. Source line numbers refer to
  the checked commit, not to the earlier reviews. A structural risk is labelled
  as such; a passing existing test is not proof that a missing case works.
- **Scope.** Re-read the cited code and the changes since `1cb03863` in the
  server, shared UI, static edition and native shell. Checked the added archive,
  bundle, document-outline, JSON, fold-dial, preview-safety and offline paths.
  Applied honey principles: remove dead code and speculative interfaces; prefer
  existing mechanisms and the standard library. No installed `codebase-design`
  skill was found. Here, a **deep module** means a small interface that hides
  substantial implementation detail, including resource lifetime and refresh.
- **Verification.** Documentation tests passed all 26 checks before and after
  the rewrite. The full pre-commit gate passed. A targeted server run passed
  488 tests covering resource containment, mutation policy,
  public mode, archive/bundle providers, previews and URLs. Model checks passed.
  Small isolated probes confirmed the failures noted below. The JSON probe used
  the actual adapter with DOM-only imports stubbed; the bundle-eviction probe
  used real temporary Git repositories. This pass did not rerun browser or
  native UI suites, deployment, load benchmarks or every advertised command.
- **Numbering.** A1–A12 retain their identities from the consolidated review.
  Old task descriptions and their earlier acceptance criteria remain history.

## Architecture as it is

- **One UI, three hosts.** [ui/][ui] is a symlink to the server package’s shared
  frontend. The static development page loads ES modules; the concatenating
  [static/build-index.py][builder] produces [static/index.html][bundle].
  [server/src/filemill/cli.py][cli] starts Uvicorn and Starlette in
  [server/src/filemill/app.py][app]. The Linux WebKitGTK prototype embeds the
  same UI and implements filesystem and history calls in
  [native/webview/main.c][native-host], lines 17–188. It is not cross-platform
  feature parity: the native FS has writes but no remove operation
  ([ui/adapters/native.js][native-adapter], lines 14–54).
- **Root-relative resources.** [server/src/filemill/urls.py][urls], lines
  31–105, accepts Raw, Rendered and Source, two column layouts, and the `?f`
  shortcut. [server/src/filemill/app.py][app], lines 393–486, resolves a real
  file and an optional virtual remainder. Bare files return bytes; other views
  return the shell. A bare directory may serve its own index. Named mounts and
  the alternate shell are gone (`03359503`, [the route removal][129]); `w` and
  `n` now name real resources. Explicit API, UI and PWA routes still shadow
  matching resources. [The route-collision task][121] owns that open design.
- **Read and write boundaries.** [server/src/filemill/paths.py][paths], lines
  19–127, resolves the root and direct-root symlink bookmarks. Public mode
  rejects dotted request components and resolved hidden targets, and filters
  listings and search. [server/src/filemill/mutations.py][mutations], lines
  33–53, checks Origin, Host, configured origins and a per-process token.
  Save and delete authorize before reading a body or changing files. Bare HTML
  remains trusted same-origin content under [SECURITY.md][security].
- **Three ports, mutable nodes.** [ui/core/ports.js][ports], lines 10–99,
  declares FS, PREVIEW and ROUTER. Optional capabilities include writes,
  deletion, raw URLs and a stale-read flag. Nodes also carry adapter-specific
  parsing and metadata state. Browser JSON, CSV and document wrappers compose
  around each filesystem. The interface hides byte access and gives JSON
  refresh invalidation to the adapter. Preview lifetime remains A9.
- **Model and DOM.** [ui/core/model/][model] owns selection, sorting, folding,
  deep links, headings, safe URLs and Markdown task changes without browser
  APIs. The surrounding core remains a DOM-coupled singleton. Columns retain
  DOM and evict off-screen rows; previews are still rebuilt (A9).
- **One fold dial.** [ui/core/model/folding.js][folding], lines 76–133, owns
  stops, windows and widened widths. [ui/core/layout.js][layout], lines
  97–303 and 396–527, owns scroll writes, settling, wheel-axis locking and
  fullscreen handoff. A remount clears old glides and gesture state. Keep
  these measured fixes and their model boundary; a new layout framework is
  not justified by this review.
- **Virtual containers.** JSON/JSONL, CSV and document headings are browser
  adapters. Large JSONL files keep byte spans; JSON documents have an 8 MiB
  parse limit. Markdown and RST sections carry line spans. Server SQLite,
  archive and Git bundle providers register in [server/src/filemill/vfs.py][vfs],
  lines 89–145. `VFSMemberProvider` adds byte reads for archive and bundle
  members. API calls keep real path `p` and member path `v` separate, but
  selection and browser history still use display names (A6, A7).
- **Rendering.** [ui/adapters/app-http.js][app-http], lines 97–187, composes
  browser Markdown, DOCX and PPTX rendering with server RST and member
  rendering. Markdown/DOCX dependencies are vendored in the server edition;
  static and native retain the download-consent setting. Source and Raw are
  shared browser capabilities, with remaining routing gaps in A8. The native
  preview still delegates directly to PreviewRich. See the
  [README edition matrix][readme] and [the native qualification][native-readme].
- **Persistence and offline reads.** Files are durable data. IndexedDB stores
  browser folder handles; localStorage stores settings; history stores
  navigation. The server worker keeps shells, assets and bounded offline read
  copies, serves live responses first except exact versioned asset hits, and
  marks offline responses. [ui/adapters/server-status.js][server-status],
  lines 80–161, probes for recovery and renews the mutation token; the HTTP
  adapter records stale reads and the editor refuses them. This is the policy
  in [ADR 0089], not a ban on cached document bytes. The static worker still
  uses the earlier policy (A5).

### What is healthy

Keep these boundaries and checks.

- The shared UI, DOM-free model and small ports avoid separate applications.
  Archive parsing uses the standard library; Git object handling uses Git.
- The preview safety fix escapes wikilink text and sanitizes converter output.
  HTML preview frames, including archive members, are sandboxed. A1–A3 are
  resolved; bare HTML serving keeps its documented trust boundary.
- [The CI workflow][ci] runs pre-commit, model checks, bundle consistency,
  separate static bundle/development suites and the server suite with branch
  coverage. Only main publishes; cancellation is scoped to workflow and ref.
  [CONTRIBUTING.md][contributing] describes the same gate. These are configured
  gates; the local results above do not claim a fresh full CI run.
- Tests use observable browser state for readiness. Delayed responses can
  supply test input, as the [waiting guidance] explains. The source guard
  rejects `wait_for_timeout`; it does not ban every sleep or prove overlap.
  Static checks live in
  [static/tests/][static-tests]. [The remaining-test record][remaining-tests]
  separates historical failures from current work. Keep the tests that guard
  log-pipe backpressure, touch input, scroll settlement and worker recovery.
- [The older-review repairs][131] fixed conditional Zstandard imports, typing
  stubs and unexplained tuning constants (`f7e917a5`). Clipboard refusal now
  offers manual copying with the full value and error (`fef28359`). Neither
  repair requires a general framework or a new service layer.

### Rules for changes

- A decision that changes a port or a behaviour gets an ADR in the same
  change. A later ADR is too late ([the decision-timing task][126]).
- Code that a change retires is deleted in the same change.
- Keep the shared UI and the concatenating builder. Do not add a framework,
  bundler, ORM, general `ViewSpec` or cache manager without a failing,
  measured case. Make existing modules deeper by hiding their invariants.
- Native qualification is already complete for the Linux prototype. Fix A9
  before expanding its preview workload; do not describe native work as still
  waiting to start. Keep changes within the issue being implemented.

## Findings

Effort: S is up to a day; M is one to three days. Split broad work into
reviewable changes with focused regressions.

| ID | P | Status | Remaining finding | Effort / risk |
| --- | --- | --- | --- | --- |
| A4 | P1 | Open | Saves can truncate or overwrite newer content | M / medium |
| A5 | P1 | Changed | Static worker freshness, misses and cache ownership | M / medium |
| A6 | P2 | Changed | Virtual identity is still a display name | M / medium |
| A7 | P2 | Changed | SQLite keys collide; provider failures look empty | M / medium |
| A8 | P2 | Changed | Preview source and representation are conflated | M / medium |
| A9 | P2 | Changed | Preview reuse and async ownership remain missing | M / medium |
| A10 | P2 | Changed | Limits still do not bound acquired work | M / medium |
| A11 | P3 | Changed | Clean-environment command audit remains unverified | M / low |
| A12 | P3 | Changed | Smaller defects, dead code and audits | S each / low |
| A13 | P2 | Resolved | JSON refresh reads the current source | S / low |
| A14 | P2 | Resolved | Active bundle reads retain repository ownership | S / medium |

### A4. Saves can truncate or overwrite newer content

**Status: open, P1.** [server/src/filemill/api.py][api], lines 358–375,
checks the size and text, then calls `target.write_bytes(data)`. Failure after
truncation can lose the old file. No revision travels from read to save.
[server/src/filemill/app.py][app], lines 354–361, buffers the entire request
before the size check and calls blocking save code on the event loop.
[ui/adapters/fsa.js][fsa], lines 70–81, has no external-change check or
explicit abort after a failed write. Native already requests consistent,
durable replacement ([native/webview/main.c][native-host], lines 151–170),
but its write port also has no expected revision.

**Acceptance.** A failed server write leaves the old bytes intact. Stale writes
fail with a conflict while retaining the draft. Specify symlink, hard-link,
ownership and permission behavior for replacement. Recheck browser-owned files
before writing and abort failed streams. Preserve [the editor task][28]’s
explicit navigation-discard policy. Authorization from A3 remains in place.

### A5. The static service worker retains the old policy

**Status: changed, P1.** The server portion is resolved by [the offline-read
work][117], commits `aa963e3a` and `54b639bb`. Its worker uses network-first
reads, valid offline misses, scoped cache cleanup and marked copies
([server/src/filemill/static/sw.js][server-sw], lines 65–199). The editor
rejects stale reads ([ui/editor/editor.js][editor], lines 26–43).

[static/sw.js][static-sw], lines 10–44 and 64–76, still shares the name
`filemill-v1`, deletes every other cache on its origin and answers from a
cached response immediately. Its `cached || networkFetch || fallback` tests a
promise: when an uncached fetch fails, the promise resolves to `null`, not to
the fallback Response. The cache name and activation cleanup also affect
other applications on a shared origin. These are source-confirmed defects;
this pass did not rerun an installed-worker reproduction.

**Acceptance.** Online reads use current content; offline copies have an
indicator. Cold offline misses return a valid response. Each static app scope
owns its cache and cleanup. Test two applications sharing an origin and an
installed upgrade from the legacy worker without losing folder handles.
Coordinate transport changes with [the route-collision task][121].

### A6. Virtual identity is still a display name

**Status: changed, P2.** This is now a demonstrated identity problem, not only
an unverified round trip. [ui/core/model/deeplink.js][model-links], lines
10–14 and 36–70, serializes names, drops empty names and finds children by
name. [ui/core/model/state.js][state], lines 54–55 and 98–100, also selects
by name. A probe walking an empty key produced no selection.

Archive and Git bundle listings truncate `name` but retain distinct `vpath`
values ([server/src/filemill/providers/archive.py][archive], lines 157–176;
[server/src/filemill/providers/gitbundle.py][gitbundle], lines 155–161).
Two archive filenames with the same first 65 characters produced one distinct
display name and two distinct virtual paths. The UI selects the first matching
name, so the second identity cannot be restored correctly. Truncation can also
remove the extension used to choose a renderer.

[ui/adapters/router-path.js][router-path], lines 22–39, encodes segments, but
server resource splitting and path resolution decode and split again
([server/src/filemill/api.py][api], lines 255–290;
[server/src/filemill/paths.py][paths], line 106). Percent signs, embedded
slashes, Unicode and empty keys need end-to-end reload checks; this pass did
not establish the full matrix. Document headings already disambiguate repeated
labels ([ui/core/model/headings.js][headings], lines 135–143).

**Acceptance.** Separate identity and presentation without inventing a general
node framework. Long names and colliding labels stay independently selectable.
Empty keys and keys containing `%`, `/` and Unicode survive selection, history,
copy and fresh reload. Keep the resolved whole-listing/row-eviction behavior.

### A7. SQLite keys collide; provider errors look empty

**Status: changed, P2.** SQLite remains open. In
[server/src/filemill/providers/sqlite.py][sqlite], lines 44–53, all listing
exceptions become `[]`. Lines 137–150 select `rowid` and use a truncated key
as both label and path. Lines 184–235 query schema and uniqueness per row.
A populated WITHOUT ROWID fixture returned no rows. Tests currently even
expect truncated keys; passing them does not prove unique identity.

The new providers repeat the error ambiguity: [server/src/filemill/providers/archive.py, lines 115–147][archive]
turns corrupt or unreadable indexes into `{}`, while [server/src/filemill/providers/gitbundle.py, lines
78–118 and 196–202][gitbundle] previously turned command failure, timeout or failed
unbundling into an empty tree. A14 now propagates these Git errors. A corrupt
ZIP probe returned `[]`.
[server/src/filemill/api.py][api], lines 209–218, further treats any provider
failure as "not browsable", although lines 233–236 can already report a
provider exception as `denied`.

**Acceptance.** With A6’s identity contract, keep SQLite keys lossless and read
schema facts once per listing. Read WITHOUT ROWID tables or report unsupported.
Distinguish empty, unsupported, corrupt and inaccessible containers. Propagate
errors through the existing API error field; do not add a general result-type
framework. Keep SQLite connections read-only. Address partial listings in A10.

### A8. Preview source and representation are conflated

**Status: changed, P2.** Shared Source/Rendered/Raw behavior for browser files
landed in `d1e98b46`; the text-only size gate is also resolved. Remaining cases:

- **Browser-owned RST.** [ui/adapters/app-http.js][app-http], lines 112–150
  and 240–249, uses the same RST override for served and local-folder nodes.
  A local handle has no `rel`, so it requests `/api/preview?p=undefined`.
  The registered browser renderer list at lines 97–101 also excludes RST.
- **Member Source mode.** The wrapper at lines 163–172 sends highlighted
  server members to `/api/preview`; [server/src/filemill/app.py][app], lines
  333–338, and [server/src/filemill/api.py][api], lines 331–355, call
  `render_preview`, not `render_source`. An RST member still renders RST;
  an HTML member still gets an iframe. The request carries no representation.
- **Native Source mode.** [ui/adapters/app-native.js][app-native], lines
  40–45, omits `withHighlighting`; [ui/adapters/native.js][native-adapter],
  lines 55–57, delegates directly to PreviewRich.

**Acceptance.** Choose a renderer from source capability and representation,
not wrapper order or the presence of a virtual path alone. Local-folder RST
makes no server preview request. Source, Rendered and Raw work for supported
file/member kinds across hosts. Reuse the renderer table and raw capability;
a general `ViewSpec` is not justified. [The RST task][41] keeps its scope.

### A9. Preview reuse and async ownership remain missing

**Status: changed, P2.** [ui/core/render.js][render], lines 476–517, creates a
new preview and revokes URLs on every render unless an editor is active.
Lines 684–730 read metadata and render again. Resize calls render from
[ui/core/layout.js][layout], lines 521–525. This resets scroll/media and repeats
provider work. The native qualification recorded 1.4–2.8 s wrapping a 400 KB
single-line source versus 10–17 ms in Chromium; those are historical figures,
not new measurements. [The preview-cache task][21] is under Completed /
Accepted but its requested reuse is absent.

`navSeq` guards choose and refresh ([ui/core/nav.js][nav], lines 57–103 and
132–174). `applyPath` has a separate boolean guard ([ui/core/deeplink.js][links],
lines 24–68), and `walkPath` mutates global state across awaits without a
shared generation. An older walk can append after a new choice or root mount.
The new offline-recovery remount is another caller
([ui/adapters/app-http.js][app-http], lines 71–79 and 175–206).

Deletion now blocks new fills and waits for active reads before removal
([ui/core/render.js][render], lines 106–145; `84214e2f`). Fold-glide resets
are fixed too. Neither fix supplies general preview or navigation ownership.

**History correction, 2026-10-21 ([the Back race][137]).** A provisional
document column could push history before its outline read declined it,
leaving an extra folder entry. URL synchronization now waits until every open
node is a loaded directory. Controlled-response browser tests cover both a
declined document and a confirmed outline. This keeps the existing model and
router boundary; A9's broader ownership and preview work remains open.

**Remount evidence, 2026-10-21.** The [Back race record][137] also records a
separate failure in the static typeahead test on unmodified main `7872f0c6`.
After a remount, the open path retained a declined `release-notes.md` node
with `dir: false`; the helper waiting for a single root column timed out.
Four isolated baseline runs passed and the fifth failed. The history guard
does not supply ownership across remounts. This existing failure blocks
integration under the red-suite rule.

**Remount correction, 2026-10-21 ([the Back race][137]).** The steward widened
that issue to include the typeahead failure. A controlled browser regression
reproduces a document choice whose grace period ends after a new root mounts:
the old choice appended its node to the new path, then declined-file cleanup
used its old column index and retained the file. `choose` now checks the
originating parent identity after the grace await. Its existing post-read
membership check handles remounts after the provisional column opened. This
local correction leaves the general `walkPath`/preview ownership work open.

**Acceptance.** Reuse the preview per node, revision, representation and relevant
settings. Resize/fold cause no new provider read. Save, refresh and mode changes
invalidate it. One generation covers choose, path walks, refresh, recovery and
remount. Each preview owns its object URLs. Delayed results cannot replace
current selection or write state through a newly installed filesystem port.

### A10. Limits still do not bound acquired work

**Status: changed, P2.** Existing limits are useful, but several checks happen
after expensive work. The earlier blanket claim that archives and bundles
bound all work was too strong.

- **Search and saves.** [server/src/filemill/api.py][api], lines 70–127,
  captures all ripgrep output before taking 100 matches. A timeout exists;
  client abort does not cancel the child. Request buffering remains in A4.
- **File reads.** [server/src/filemill/preview.py][preview], lines 74–77 and
  201–205, reads whole files before validating or slicing. Rich previews fetch
  the blob before their text gate ([ui/adapters/preview-rich.js][rich], lines
  461–465 and 497–509). Native reads and base64-encodes the whole file on the
  host callback ([native/webview/main.c][native-host], lines 141–150).
- **Archives and bundles.** [server/src/filemill/providers/archive.py, lines 95–140 and 199–211][archive]
  limits accepted distinct index entries, not every scanned tar record or
  decompressed byte. ZIP loads its central directory before the loop limit.
  Directory listing invokes this work through `_opens_as_folder` even before
  an archive is opened. Bundle input and blob size limits and per-call timeouts
  do not cap unbundling disk expansion or captured tree output
  ([server/src/filemill/providers/gitbundle.py, lines 94–118 and 196–213][gitbundle]).
- **Browser work.** PPTX decompression and DOCX conversion have no expanded-byte
  limit ([ui/adapters/preview-rich.js][rich], lines 378–457). Large JSONL
  indexing bounds eager parsing, but still makes one span and node per row
  ([ui/adapters/vfs-json.js][json], lines 85–134 and 260–264). Metadata sweeps
  start all reads with `Promise.all` ([ui/core/sort.js][sort], lines 62–83).

**Acceptance.** Enforce byte, record, expansion and deadline limits where work
is acquired, and report partial results. Reap subprocesses on budget, timeout
or cancellation. Keep truncated text non-editable. Measure before adding pools
or broader caches. Preserve the existing JSON byte and fold-depth guards.

### A11. The command audit remains unverified

**Status: changed, P3 (previously P2).** The named documentation contradictions
have been corrected; their resolving commits are recorded below. This finding
no longer asserts that the current README advertises the retired renderer.
The remaining acceptance is a clean-environment run of every advertised
command. The 26 documentation tests check selected claims and portability;
they do not establish that full audit.

**Acceptance.** Keep documents current with each fix. Separately smoke-test
advertised commands under their documented prerequisites and distinguish
historical measurements from current instructions. Do not block A4–A10 on
this final audit, or repeat already completed roadmap and ADR rewrites.

### A12. Smaller defects, dead code and audits

**Status: changed, P3.** Each remaining item is independent.

- **Open: folder persistence.** [ui/adapters/storage.js][storage], lines
  45–67, returns before the IndexedDB transaction completes and performs
  read-modify-write across awaits. Concurrent tabs can lose recent-root updates.
- **Changed: unused interfaces.** The bad integer query failure is resolved,
  but [server/src/filemill/app.py][app], lines 53–54, retains an unused integer
  conversion branch. [server/src/filemill/vfs.py][vfs], lines 134–136, has no
  production caller for `is_vfs_file`. [server/src/filemill/preview.py][preview],
  lines 82–100 and 129–153, retains an unused state argument and a source helper
  called by tests but no route. Re-check callers before deleting them.
- **Open: repeated and verbose glue.** Preview-error HTML is hand-built in
  seven server sites. [ui/adapters/vfs-json.js][json], line 22, imports render
  without using it; [ui/adapters/router-path.js][router-path], line 15, imports
  state path without using it. Remove dead imports and comments that restate
  code as the affected modules change. Do not replace a few error strings with
  a templating framework. Preserve comments about measured browser behavior.
- **Open: dependency direction.** [ui/core/search.js][search], lines 25–39,
  builds an HTTP API URL in core. Classification and VTT parsing remain in both
  languages; [server/src/filemill/vfs.py][vfs], line 15, and
  [ui/core/limits.js][limits] disagree on image extensions. Compare behavior
  before introducing cross-language generation.
- **Open: provider discovery.** Registration order is still an import side
  effect ([server/src/filemill/vfs.py][vfs], lines 123–145). Missing Git silently
  leaves bundles plain; missing ripgrep reports per request. Expose useful
  capability failures without building a plugin system.
- **Open: accessibility.** Rows are clickable divs with labels, without full
  list/tree semantics ([ui/core/render.js][render], lines 300–354). An assistive
  technology audit remains outstanding.

### A14. Bundle eviction removes an active repository

**Status: resolved, P2, 2026-10-21.** Tree and blob reads retain the
`TemporaryDirectory` owner through their last Git call in
[server/src/filemill/providers/gitbundle.py][gitbundle]. The eight-entry cache
releases only its own reference on eviction. Cleanup waits for the final
active reader. Git failures and timeouts propagate through the existing
provider error path; a listing reports `denied`. Other A7 work remains open.

[The bundle provider regressions][bundle-tests] force eviction before a tree
read and between blob metadata and content. A two-reader test checks that
cleanup waits for both readers. Tests also check command failures and the
unchanged deadline and Git configuration isolation. [ADR 0073] records the
lifetime rule.

## Resolved since the earlier reviews

Do not reopen these without new evidence. Resolved portions of changed
findings are separated from their remaining acceptance above.

### A13. JSON-column refresh keeps the old parsed value

**Status: resolved, former P2; 2026-10-21.** Refresh now awaits the FS
adapter's optional `invalidate(node)` hook before `ensureLoaded`. The JSON
adapter clears its parsed value, file bytes, metadata and parse errors. A
nested column resolves its path from the current source. The core does not
need parser-specific fields. [The port decision][ports-decision] defines the
contract.

The existing selection walk closes removed paths and renders the new preview.
Parse failures show an error and current source text, without old values.
Browser regressions cover edits, removed keys and invalid JSON in root and
nested columns, plus real files and changed ZIP members in served mode.
The static bundle and development modules use the same adapter. This does
not resolve A9's broader navigation and preview ownership work.

### A1. The directory index escapes the root check

**Status: resolved, former P1.** `e02a6ef4`, [the containment and mutation
repair][103], validates the final index against request zones. Current evidence:
[server/src/filemill/app.py][app], lines 461–467, and the index symlink matrix
in [server/tests/test_resource_safety.py][safety-tests], lines 303 onward.
In-root indexes and direct-root bookmark targets still work. [The mount-route
removal][129] removed obsolete route cases without removing containment.

### A2. Preview content can execute as Filemill

**Status: resolved, former P1.** `7a7c41f0`, [the inert-preview repair][104],
replaced wikilink HTML injection with escaped tokens and sanitized converter
output. See [ui/adapters/preview-rich.js][rich], lines 245–278, 342–374 and
452–457; [ui/core/model/safe-url.js][safe-url], lines 7–11; and
[server/src/filemill/preview.py][preview], lines 39–52 and 201–219.
`c081ffb4`, [the archive iframe repair][114], added the missing sandbox to
server-rendered HTML members, now at preview lines 237–242. Browser HTML has
its sandbox at [ui/core/renderers.js][renderers], lines 174–180.

PDF frames remain unsandboxed and use PDF media types. That is a remaining
audit surface, not evidence that the fixed Markdown/HTML exploit is open.
All entry points still expose debug core state; same-origin scripts retain
its authority. [SECURITY.md][security] explicitly retains bare-HTML trust.

### A3. Mutations accept unrelated-origin requests

**Status: resolved, former P1.** `e02a6ef4`, [the mutation-policy repair][103].
[server/src/filemill/mutations.py][mutations], lines 33–53, validates Origin,
Host and token, including configured proxy origins and duplicate-header
rejection. [server/src/filemill/app.py][app], lines 354–378, applies it before
save/delete. [server/tests/test_mutation_policy.py][mutation-tests] covers
refusal before body reads and authorized local/proxy operations. This is
browser request authorization, not user authentication or safe file replacement.

### Resolved portions and retained earlier repairs

| Earlier finding | Status and resolving evidence |
| --- | --- |
| A5, server worker and offline misses | Resolved by `aa963e3a`, `54b639bb`, [the offline-read task][117] and [ADR 0089]; static worker remains A5. |
| A6, paged listings and retained off-screen rows | Resolved by `30cbef21` and `140a7045`; [ADR 0068]. |
| A8, browser view toggles and Raw capability | Resolved by `d1e98b46`; [ADR 0077]. Remaining host/member cases are A8. |
| A9, deletion racing active preview reads | Resolved by `84214e2f`; [ADR 0078]. General async ownership remains A9. |
| A10, excessive JSON fold recursion | Resolved by `75da49f0`; [ADR 0080]. This is not a general byte/work bound. |
| A11, edition and renderer claims | Resolved by `06b3f773`, [the edition-documentation repair][105]. |
| A11, roadmap and superseded ADR claims | Resolved by `9e048d1a`, [the roadmap correction][107], and `f488ccab`, [the documentation audit][109]. |
| A11, Playwright command drift | Resolved by `b279fdcf` and `db58f5ee`; guarded by [server/tests/test_docs.py][docs-tests]. |
| A11, consent, skip, dependency and icon claims | Resolved by `85506592`, `111f17be`, `a72c8a6c` and `08080982`; no renderer-route or dependency-version fix is implied. |
| A12, bad integer page query | Resolved by `30cbef21`, which removed the page parameter; the unused conversion branch remains. |
| A12, browser JSON path allowance | Resolved by `8ef10c6a`; [ADR 0071]. Real-file containment and virtual identity are separate. |
| Red suites, false-green scripts and missing lint gate | Resolved in the earlier gate repairs (`86651fa6`, `8b0fff25`); current configuration is [the CI workflow][ci]. See [the test record][remaining-tests]. |
| Half-deleted HTMX finder and missing module boundary | Resolved by `a6535049`, `686cd25d` and `f6d4b081`; retired routes/helpers remain absent. [ui/][ui] is ES modules and the builder follows their imports. |
| JSON key order and descending sort | Resolved by `e1928730` and `b3fc7f53`; [ui/core/model/state.js][state], lines 41–51, honors provider order and reverses descending groups. |
| Duplicated browser limits, missing mobile rules | Resolved by `3d71a45c` and `d2135ad1`; [ui/core/limits.js][limits] and [ui/core/styles.css][styles]. Python/browser differences remain A12. |
| FSA deletion and deletion-success status | Resolved by `df47ce42` and `8f95812b`; [ui/adapters/fsa.js][fsa], lines 84–92, and [ui/core/render.js][render], lines 134–152. |
| Large images rejected by the text limit | Resolved by `a275ab89`; [ui/adapters/preview-local.js][preview-local], lines 35–41. |
| Folder history and modified arrows | Resolved by `3bd91e00` and `a33cb269`; [ADR 0050]. |
| Wildcard bind and permissive CORS | Resolved by `499222cf` and `6c294f4a`; [server/src/filemill/cli.py][cli] defaults to loopback and current routes add no CORS headers. Mutation authority is A3. |
| Missing project/legal documents and retired hot-reload/storage helpers | Resolved by `916ad489`, `7dd91c3e` and `6f26dd02`; current root documents are present and retired helpers remain absent. |
| Wrapped/clipped status items | Resolved by `7232c17e` and `ae76decc`; [ADR 0074]. |

## Remediation order

Keep P1 work first. The resolved containment and preview-injection repairs are
regression requirements, not new implementation steps.

1. **Protect saves (A4).** Add atomic server replacement and revisions across
   supported write ports. Enforce request-size limits while reading. Retain
   drafts on conflict. This no longer waits for A1/A3: both are resolved.
2. **Repair the static worker (A5).** Fix freshness, valid offline fallback,
   scoped ownership and installed upgrades. Preserve the server’s accepted
   offline-copy policy. Coordinate routing/cache classification with
   [the route-collision task][121]; its transport choice remains a decision.
3. **Keep bounded repository lifetime (A14, resolved).** Each Git read retains
   its repository owner. Keep the eviction and concurrent-read regressions.
   A13's JSON refresh invalidation is resolved by [the JSON refresh repair][134].
4. **Make identities lossless (A6), then fix SQLite (A7).** Establish the
   address/label contract before changing SQLite keys. Provider error reporting
   can proceed independently through the existing `denied` field.
5. **Separate source from representation (A8).** Pin local RST, native Source
   and member Source behavior with regressions. Reuse existing capabilities.
6. **Give async navigation and previews one owner (A9).** Establish the
   generation and lifetime rules, then retain previews with an explicit
   invalidation key. A8 supplies representation identity; A13 supplies fresh
   parsed contents. Cover recovery/remount as well as normal navigation.
7. **Bound acquisition (A10).** Search, archives/bundles, rich documents and
   native reads can be separate changes. Urgent measured resource failures need
   not wait for A8/A9. Report partial results and preserve complete-file editing.
8. **Finish the audit (A11, A12).** Correct documents with each change; run the
   clean-environment command audit last. Small dead-code, persistence and
   accessibility repairs can land independently with focused checks.

## Draft issues

These are drafts for the steward, not newly filed tasks. Each corresponds to
one new P2 finding; no new P1 finding was established in this pass.

### A13 draft

- **Status:** Resolved by [the JSON refresh repair][134] on 2026-10-21.
  The requirements below retain the original draft.
- **Title:** Refresh JSON columns from current source bytes.
- **Why:** The JSON column’s refresh rebuilds from a retained parsed value,
  so an external edit remains invisible while the UI reports no change.
- **What to change:** Give the virtual adapter ownership of invalidation and
  re-read the backing file/member before rebuilding its children. Coordinate
  navigation/preview invalidation with A9; do not teach core every parser field.
- **Acceptance:** Failing regressions first for an open JSON column after an
  external edit, removed key, parse failure and changed archive member. The
  column’s own refresh reads again, updates preview and selection, and reports
  errors instead of retaining stale values. Static/development and served
  modes agree. Update the relevant port decision and documentation with the fix.

### A14 draft

- **Status:** Resolved on 2026-10-21. The requirements below retain the
  original draft.
- **Title:** Keep bundle repositories alive through active reads.
- **Why:** The eight-entry cache owns temporary repositories, while requests
  keep only paths. Eviction can turn a live read into an empty tree or missing
  member.
- **What to change:** Retain the cached temporary-directory owner until all Git
  calls for that request finish. Keep cleanup tied to ownership and the existing
  bounded cache. Surface genuine command failure through A7’s error path.
- **Acceptance:** Failing regressions first that evict the acquired entry before
  a tree read and between a blob’s metadata/content calls. Both reads finish
  with correct data; the directory disappears only after its final owner is
  released. Include a concurrent-request case, preserve read-only behavior and
  command deadlines, and update [ADR 0073] with the lifetime rule.

[132]: tasks/132-re-check-the-architecture-review-against-current-main.md
[134]: tasks/134-refresh-json-columns-from-the-current-file-architecture-review-a13.md
[21]: tasks/21-cache-preview-element.md
[28]: tasks/28-editor-features.md
[41]: tasks/41-rst-rendering-regression.md
[103]: tasks/103-close-the-directory-index-path-escape-and-authorize-save-and-delete-a1.md
[104]: tasks/104-make-preview-content-inert-wikilink-text-and-docx-output-a2.md
[105]: tasks/105-correct-the-current-edition-and-renderer-documentation-roadmap-phase-0.md
[107]: tasks/107-date-superseded-roadmap-and-adr-claims-roadmap-phase-0.md
[109]: tasks/109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md
[114]: tasks/114-sandbox-html-previews-of-archive-members-as-security-md-promises.md
[117]: tasks/117-clarify-cache-and-recovery-claims-from-docs-question-2.md
[121]: tasks/121-clarify-api-path-collisions-from-docs-question-6.md
[126]: tasks/126-align-decision-timing-rules-from-docs-question-12.md
[129]: tasks/129-remove-the-obsolete-w-and-n-url-routes.md
[131]: tasks/131-close-the-gaps-found-in-five-older-review-items.md
[goals]: GOALS.md
[tracker]: ../TASKS.md
[readme]: ../README.md
[security]: ../SECURITY.md
[contributing]: ../CONTRIBUTING.md
[remaining-tests]: testing/remaining-red-tests.md
[ui]: ../ui/
[model]: ../ui/core/model/
[builder]: ../static/build-index.py
[bundle]: ../static/index.html
[static-tests]: ../static/tests/
[cli]: ../server/src/filemill/cli.py
[app]: ../server/src/filemill/app.py
[api]: ../server/src/filemill/api.py
[paths]: ../server/src/filemill/paths.py
[mutations]: ../server/src/filemill/mutations.py
[urls]: ../server/src/filemill/urls.py
[vfs]: ../server/src/filemill/vfs.py
[preview]: ../server/src/filemill/preview.py
[archive]: ../server/src/filemill/providers/archive.py
[gitbundle]: ../server/src/filemill/providers/gitbundle.py
[sqlite]: ../server/src/filemill/providers/sqlite.py
[native-host]: ../native/webview/main.c
[native-readme]: ../native/README.md
[native-adapter]: ../ui/adapters/native.js
[app-native]: ../ui/adapters/app-native.js
[app-http]: ../ui/adapters/app-http.js
[fsa]: ../ui/adapters/fsa.js
[json]: ../ui/adapters/vfs-json.js
[router-path]: ../ui/adapters/router-path.js
[server-status]: ../ui/adapters/server-status.js
[storage]: ../ui/adapters/storage.js
[rich]: ../ui/adapters/preview-rich.js
[preview-local]: ../ui/adapters/preview-local.js
[ports]: ../ui/core/ports.js
[folding]: ../ui/core/model/folding.js
[headings]: ../ui/core/model/headings.js
[model-links]: ../ui/core/model/deeplink.js
[state]: ../ui/core/model/state.js
[safe-url]: ../ui/core/model/safe-url.js
[layout]: ../ui/core/layout.js
[links]: ../ui/core/deeplink.js
[nav]: ../ui/core/nav.js
[render]: ../ui/core/render.js
[renderers]: ../ui/core/renderers.js
[search]: ../ui/core/search.js
[sort]: ../ui/core/sort.js
[limits]: ../ui/core/limits.js
[styles]: ../ui/core/styles.css
[editor]: ../ui/editor/editor.js
[server-sw]: ../server/src/filemill/static/sw.js
[static-sw]: ../static/sw.js
[ci]: ../.github/workflows/publish.yml
[safety-tests]: ../server/tests/test_resource_safety.py
[mutation-tests]: ../server/tests/test_mutation_policy.py
[docs-tests]: ../server/tests/test_docs.py
[ADR 0050]: adr/0050-history-pushes-on-entering-a-column-rewrites-otherwise.md
[ADR 0068]: adr/0068-scroll-whole-directory-listings.md
[ADR 0071]: adr/0071-bounded-json-documents.md
[ADR 0073]: adr/0073-git-bundles-browse-by-refs-and-trees.md
[ADR 0074]: adr/0074-status-strip-drops-whole-hints.md
[ADR 0077]: adr/0077-preview-views-and-raw-links-work-without-routing.md
[ADR 0078]: adr/0078-delete-waits-for-active-preview-reads.md
[ADR 0080]: adr/0080-json-past-a-fold-depth-limit-is-source.md
[ADR 0089]: adr/0089-an-offline-server-shows-older-copies-with-an-indicator.md
[ports-decision]: adr/0041-core-adapters-three-ports.md#refresh-invalidation-2026-10-21
[bundle-tests]: ../server/tests/test_gitbundle_provider.py

[waiting guidance]: ../server/CONTRIBUTING.md#wait-for-an-element-never-for-a-duration
[137]: tasks/137-fix-the-intermittent-back-failure-in-test-back-retraces-the-folders-th.md
