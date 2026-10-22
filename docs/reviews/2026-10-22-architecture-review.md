# Architecture review, 2026-10-22

Reviewed main `c6fcd0e97964f7855d2902d53c23cce87f6e7943` for
[the architecture review task]. All source line numbers below refer to that
commit. Repository-relative links open the current files; use the recorded
commit when later edits move the evidence.

Keep the shared UI, three ports, DOM-free model and small native host. The
best near-term savings come from removing an unused renderer, moving repeated
SQLite work out of a row loop, and hiding the common boot sequence. A new
framework, plugin system or general virtual-node hierarchy would add work.

This supplements [the existing architecture review]; it does not replace its
correctness findings or resolve them. The brief's claim that no architecture
review exists is outdated. The [documentation review] and [security review]
already cover their respective subjects. No security probes, exploit
reproductions, application changes or new tracker issues were made here.

## Method and coverage

Applied the installed `honey` skill: remove speculative options, unused code
and repeated glue; prefer the standard library and existing mechanisms.
`codebase-design` was not available in this session. Its requested vocabulary
is used here as follows: a **deep module** has a small interface that hides
substantial work and its invariants. **Information leakage** makes callers
understand those internals. **Temporal coupling** makes them repeat operations
in a required order. A shorter source file alone is not a deeper module.

Read the project guides, goals, roadmap, prior reviews, relevant decisions
and task records before tracing these paths:

- **Server:** startup, route dispatch, path resolution, listing, search,
  mutations, preview dispatch, PWA responses and all four provider modules.
  Compared API/provider tests with the paths actually called by routes.
- **Shared UI:** the three host compositions, FS/preview/router ports,
  HTTP/FSA/native adapters, JSON/CSV/document wrappers, search, navigation,
  model state, layout, preview retention and editor snapshot handling.
  Read model checks and focused served/static regressions around these seams.
- **Static:** [static/build-index.py], development entry, worker, fixtures and
  renderer/preview tests. The generated bundle is an output, not a second
  application to refactor independently.
- **Native:** [native/webview/main.c], build entry, bridge adapter, WebDriver
  support and contract tests. No new native performance qualification is
  claimed.

Caller searches distinguished application calls from tests and historical
documents. Rankings below estimate maintenance benefit per implementation
hour, including focused tests and documentation. They are not severity scores
or measured latency improvements. Estimates apply to the bounded drafts,
not to completing all of A5–A12.

## Boundaries to retain

- **Shared search is already a deeper module.** [ui/core/search.js], lines
  15–78, owns cancellation and result actions; [ui/core/mount.js], lines
  7–18, binds the current FS capability. [ui/adapters/http.js], lines 59–74,
  and [ui/adapters/fsa.js], lines 32–126, own different ways to acquire data.
  Keep those separate implementations behind one contract. Uploading local
  bytes or introducing a cross-language search framework would undo the
  benefit of [shared content search] and [the search decision].
- **Model and renderer separation pays for itself.** Keep the DOM-free
  [ui/core/model/] and actual browser rendering tests. Keep preview retention
  in [ui/core/render.js], lines 503–547, and the reuse regressions in
  [static/tests/test_ui.py], lines 3434–3613. Splitting the large render file
  by line count would leave its ownership problems intact.
- **Use the libraries already doing the work.** Archive parsing uses
  `tarfile`/`zipfile`; Python desktop-file parsing uses `ConfigParser` in
  [server/src/filemill/preview.py], lines 458–473. Git bundle object access
  uses Git and retains its temporary repository owner through active reads
  in [server/src/filemill/providers/gitbundle.py], lines 108–120 and 197–211.
  Keep these boundaries and their lifetime tests. No additional parser,
  cache manager or ORM is justified.
- **The small builder and native bridge have real callers.**
  [static/build-index.py], lines 60–107, follows a constrained module graph
  and rejects unsupported imports and declaration collisions. Preserve that
  constraint when moving code. [native/webview/main.c], lines 82–171,
  translates host operations for the same UI. Its adapter and test driver
  serve an existing edition; they are not speculative cross-platform work.

## Ranked findings

- **F1 — The Python WebVTT renderer has no route.** Highest deletion benefit;
  about 1 hour, low risk if the small provider contract is retained.
  [server/src/filemill/providers/vtt_provider.py], lines 16–80 and 90–122,
  implement a second parser and renderer, including unused page/limit/column
  arguments. Calls to that renderer are in
  [server/tests/test_vtt_provider.py], lines 11–79. The application renderer
  is [ui/core/renderers.js], lines 33–90 and 190–194; the server dispatch in
  [server/src/filemill/preview.py], lines 298–319, never calls the provider's
  renderer. This duplicates format maintenance without supplying a feature.

  **Recommendation:** move the useful transcript cases to the live JavaScript
  renderer, then remove the Python parsing/rendering code. Keep the provider's
  `handles`, empty `list_entries` and registration in this change: removing
  them also changes `/api/dir` responses and virtual-suffix URL recognition
  ([server/src/filemill/api.py], lines 268–290 and 312–328). About 100 lines
  of unused implementation can go without changing those responses.

  **Overlap:** a concrete deletion slice of A12's cross-language/dead-code
  audit, also noticed in [the earlier documentation reconciliation]. Draft D1
  refines that work; it is not a new WebVTT feature or a reopened transcript bug.

- **F2 — SQLite derives table facts once per row.** High benefit; about
  1 hour, low-to-medium risk. [server/src/filemill/providers/sqlite.py],
  lines 137–159, calls `_row_key` for each row. Lines 184–186 query the schema
  each time; lines 215–230 can also run the same two uniqueness queries each
  time. A 500-row table without a primary key can therefore incur 1,500
  schema/uniqueness queries in addition to listing work. This is a source
  count, not a timing result.

  **Recommendation:** derive the key choice once inside `_list_rows`, then
  format rows from those facts. The listing operation should hide its database
  work; a row formatter should not need a connection. Keep the current labels,
  order, row limit and error behavior in this slice. It removes repeated work
  and makes query-count testing possible without a browser.

  **Overlap:** A7 already asks for schema facts once per listing. Draft D2 is
  its bounded performance slice. Lossless identities and WITHOUT ROWID support
  remain separate A6/A7 work; this draft does not claim to fix them.

- **F3 — Every host knows the core boot sequence.** Resolved on 2026-10-22 by
  [the shared boot task]. [The core initializer] now owns the seven calls;
  each host calls it once after shell creation. Host choices stay at the
  composition sites. The original finding follows for context.

  High recurring maintenance benefit; about 1 hour, medium risk from
  import/initialization order.
  [ui/adapters/app-fsa.js], lines 68–76,
  [ui/adapters/app-http.js], lines 83–91, and
  [ui/adapters/app-native.js], lines 32–38, repeat the same seven calls for
  sorting, action wiring, deep links, layout and settings. Adding a core
  initialization step requires editing all hosts. This is temporal coupling
  leaking across the adapter boundary.

  **Recommendation:** give those three callers one explicit core initializer
  that owns the fixed sequence. Leave renderer registration, port selection,
  welcome screens, persistence and root acquisition in the host compositions.
  This is an abstraction with three present callers and a hidden ordering
  invariant; it does not need a configurable application class or lifecycle
  framework. Delete the repeated blocks and obsolete classic-script narration
  in the same change.

  **Overlap:** no matching active implementation task was found. This extends
  the existing three-port design; it does not reopen the native-shell choice
  or [browser fixture isolation]. Draft D3 is the new independent proposal.

- **F4 — Preview composition confuses kind with source.** High user benefit,
  but constrain the first change to about 1 hour. In
  [ui/adapters/app-http.js], lines 146–162, an ordinary RST node selects
  `PreviewHTTP` by kind and absence of `vpath`. The Open Folder composition
  reuses that wrapper at lines 250–260. An FSA node has a handle, not `rel`
  ([ui/adapters/fsa.js], lines 20–27); the HTTP renderer nevertheless builds
  its request from `n.rel` at lines 119–126 of the host composition. The
  source boundary is encoded indirectly in wrapper order and node fields.

  **Recommendation:** keep server rendering in the served composition and
  select browser-owned preview behavior explicitly when mounting local files.
  For the first slice, preserve the bounded Source fallback for local RST
  without issuing the invalid server request. Reuse JSON/CSV/document wrappers
  rather than introducing a general `ViewSpec`. This reduces source-specific
  branching and makes provider-choice tests independent of a live server.

  **Overlap:** A8 and the documentation review already identify this defect.
  Draft D4 refines A8, not a second issue. Registering browser RST also affects
  download-switch visibility ([ui/adapters/preview-rich.js], lines 44–57 and
  79–99), [the preview-switch task] and [the consent decision task]. Do not
  silently enable Pyodide downloads in this slice. Full local RST rendering,
  member Source and native Source remain A8 follow-ups.

- **F5 — A path walk does not own its mount or lifetime.** High correctness
  benefit; about 1 hour for the remount slice, medium risk. In
  [ui/core/deeplink.js], lines 59–71, `applyPath` passes a callback that reads
  the mutable global `FS` after each await; a boolean suppresses URL writes.
  [ui/core/model/deeplink.js], lines 46–70 and 82–87, mutates global selection,
  path and focus across awaits. [ui/core/mount.js], lines 13–18, can replace
  that root. `choose` has its own sequence and parent check in
  [ui/core/nav.js], lines 57–103; those checks do not cover `walkPath`.
  This is a source-confirmed ownership gap, not a newly reproduced race.

  **Recommendation:** make a path walk own a captured filesystem, root and
  validity check. Stop before committing state after a remount, including its
  final focus/render work. Hide that rule in the navigation operation instead
  of asking every caller to repair state afterwards. Use controlled promises
  in model tests, not timing sleeps.

  **Overlap:** Draft D5 is one bounded A9 repair. It preserves the completed
  [history/remount repair] and [preview reuse repair]. Unifying every choice,
  refresh, preview and object-URL lifetime is larger than this draft and remains
  in A9; no new general task scheduler is proposed.

- **F6 — Unused glue creates misleading dependencies.** Smaller benefit;
  about 0.5–1 hour, low risk. [ui/adapters/vfs-json.js], line 22, and
  [ui/adapters/vfs-csv.js], line 3, import `render` without calling the imported
  binding. [ui/adapters/router-path.js], line 15, imports unused state `path`;
  its `write` parameter at line 33 is a different binding. These imports pull
  UI state into modules that do not need those edges. On the server,
  [server/src/filemill/app.py], lines 26–27 and 69–70, retains `_HTML_EXTS` and
  integer conversion although no registered route parameter is an integer.
  [server/src/filemill/vfs.py], lines 134–136, exposes `is_vfs_file` only to
  its tests in [server/tests/test_vfs.py], lines 169–185.

  **Recommendation:** remove these exact unused edges and branches after
  rechecking callers. Keep the small route adapter's used dispatch behavior;
  replacing it with a new routing framework is not a useful one-hour cleanup.
  Preserve comments explaining browser measurements and resource ownership.

  **Overlap:** Draft D6 refines A12. Do not also delete `render_source`, its
  highlighting helpers, or Pygments: the documentation review's ADR drift and
  A8's member Source gap need a coordinated decision. Tests calling a helper
  do not establish that a user-facing route supplies that behavior.

## Existing work and exclusions

- **Shared search:** the brief calls [shared content search] In Progress;
  the checked main records it Completed / Accepted, unchecked. Its source
  boundaries and delayed-result tests are present. No duplicate draft. The
  process-per-file search tradeoff is explicit in [the search decision];
  batching needs measurements before another abstraction.
- **Test ownership:** [browser fixture isolation] is still In Progress.
  [conftest.py], lines 7–16, provides shared Playwright entry points while
  [server/tests/test_browser_keyboard.py], lines 211, 417 and 445, starts its
  own lifecycle. Root fixtures at [conftest.py], lines 20–40 and 44–65, mutate
  one application's state. Keep fixture/root qualification under that task.
  A factory for every application/service is not justified merely by seeing
  global state; first complete the existing isolation work.
- **Offline and acquisition limits:** [static/sw.js], lines 35–44 and 64–76,
  still has the A5 cleanup/miss policy. Archive discovery in
  [server/src/filemill/api.py], lines 239–256, and whole native reads in
  [native/webview/main.c], lines 151–171, remain A10 topics. Keep the separate
  hosts' caching requirements; do not copy the server worker wholesale or add
  a generic cache manager. These are existing findings, not new drafts here.
- **Other ownership:** route collisions belong to [the route-collision task];
  consent policy belongs to [the consent decision task] and docs Q1. Docs Q2
  owns numerical roadmap budgets. A6/A7 own virtual identity; A12 already owns
  folder-persistence transactions and provider-discovery cleanup. The security
  review and its linked repairs retain their findings. None is reopened by
  this architecture-only pass, and no security acceptance is claimed.

## Validation

The unchanged baseline and the new report both passed all **33
documentation/review-condition tests** with:

```bash
timeout 600 uv run --project server pytest -q server/tests/test_docs.py server/tests/test_review_conditions.py
```

The full pre-commit gate passed all seven hooks. A separate check verified
all 45 local reference destinations, heading lengths and the six finding/draft
pairs. Guarded command measurements are recorded in
[the architecture review task]. No browser suite, native build, full runtime
suite, live-instance check or benchmark is part of this review. Findings are
static evidence; proposed fixes require their own red-green regressions.

## Draft issues

These six drafts are for the steward; none has been filed. D1, D2, D4, D5 and
D6 refine existing findings, so attach their work to those findings rather
than creating competing issues. Each estimate includes focused verification
and same-change documentation. Add an ADR whenever a port or behavior changes.

- **D1 — Retire the unreachable Python WebVTT renderer.** About 1 hour;
  F1, existing A12. **Work:** transfer meaningful parser fixtures to tests
  exercising the registered JavaScript VTT renderer; remove Python `parse`,
  its helpers, `default_fmt` and `render_preview`. Keep the small empty-listing
  provider and its registration. Update the provider test/source map.
  **Acceptance:** timestamps, voices, YouTube metadata/blank payloads, malformed
  input and source preservation retain coverage on the live implementation;
  ordinary VTT listing, raw bytes, empty virtual listing and suffix URLs retain
  their responses. No application code calls the deleted renderer. Do not
  replace it with a cross-language parser generator.
- **D2 — Compute SQLite row-key facts once per listing.** About 1 hour;
  F2, existing A7. **Work:** add a failing query-count regression; derive schema
  and first-column uniqueness before the row loop; format keys from the result.
  **Acceptance:** one table-schema query and at most two uniqueness queries
  per listing, independent of row count; supported PK/composite-PK/fallback
  labels, records, order and 500-row marker remain unchanged. Run focused
  provider/API checks. Do not change identity encoding or add an ORM.
- **D3 — Centralize the shared UI boot sequence.** About 1 hour; F3, new.
  **Work:** replace the three identical initialization blocks with one core
  initializer; leave host-specific choices at the three call sites. Remove
  narration about the retired classic-script loading order.
  **Acceptance:** one implementation of the seven-call sequence; each host
  calls it once after shell creation. Existing mount, keyboard, sorting and
  preview checks retain their behavior. Check static development/bundle and
  native composition through their existing entry points; rebuild the static
  bundle and retain import/collision checks. No configuration class, event bus
  or host inheritance tree is added.
- **D4 — Keep server preview dispatch out of local mounts.** About 1 hour;
  F4, existing A8; coordinate with the preview-switch task and consent decision.
  **Work:** first make a controlled local RST provider-choice test fail; give
  local and served compositions explicit preview selection. Keep local RST's
  existing bounded Source fallback and current download policy.
  **Acceptance:** local RST makes no server-preview request, including for a
  section; served RST still uses Python; Markdown/DOCX/PPTX and virtual records
  keep their renderer. No newly enabled third-party download or upload. Update
  the adapter guide and affected documentation checks. Full local Rendered RST
  remains explicitly unsupported until the remaining A8 work is done.
- **D5 — Stop a deep-link walk when its root is replaced.** About 1 hour;
  F5, existing A9. **Work:** add a deferred-load regression that mounts a new
  root while `walkPath` is waiting. Capture the originating FS/root; check
  validity after each await and before final state/render effects.
  **Acceptance:** releasing the old read changes no new-root selection, path,
  focus or URL and issues no read through the replacement FS. Normal complete,
  truncated and declined-document walks still pass. Keep choose/refresh and
  preview reuse guards; record that broader generation ownership remains open.
- **D6 — Remove unused adapter edges and server glue.** About 0.5–1 hour;
  F6, existing A12. **Work:** recheck callers, remove the three dead imports,
  `_HTML_EXTS`, unused integer conversion and internal `is_vfs_file` helper;
  retire tests that only assert the removed wrapper and keep registry behavior
  checks. **Acceptance:** development and bundled module graphs still load;
  current string/default/path query dispatch and provider lookup tests pass;
  no replacement abstraction or behavior change. Update A12's exact remaining
  list, leaving Source routing decisions to A8.

**Recommendation:** do **D1, D2 and D3 first**, in that order. D1 removes a
second implementation with no route; D2 removes repeated database work behind
one existing operation; D3 prevents three-host boot drift. These are bounded
changes with clear evidence and no consent or URL-design decision. D4 and D5
then reduce source/lifetime leakage within A8/A9; D6 is a small cleanup to
combine with work in those modules when convenient.

[the architecture review task]: ../tasks/149-review-filemill-s-architecture-for-deep-modules-and-over-engineering-a.md
[the existing architecture review]: ../ARCHITECTURE-REVIEW.md
[documentation review]: 2026-10-22-docs-review.md
[security review]: 2026-10-21-security-review.md
[the earlier documentation reconciliation]: ../tasks/109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md
[shared content search]: ../tasks/130-give-served-and-browser-owned-folders-the-same-content-search.md
[browser fixture isolation]: ../tasks/141-finish-browser-fixture-isolation-and-qualify-independent-test-roots.md
[the search decision]: ../adr/0092-shared-content-search-capability.md
[the preview-switch task]: ../tasks/118-hide-the-ineffective-server-preview-switch-from-docs-question-3.md
[the consent decision task]: ../tasks/125-clarify-network-consent-scope-from-docs-question-11.md
[history/remount repair]: ../tasks/137-fix-the-intermittent-back-failure-in-test-back-retraces-the-folders-th.md
[preview reuse repair]: ../tasks/140-reuse-the-preview-element-across-resizes-and-folding.md
[the route-collision task]: ../tasks/121-clarify-api-path-collisions-from-docs-question-6.md
[static/build-index.py]: ../../static/build-index.py
[static/sw.js]: ../../static/sw.js
[static/tests/test_ui.py]: ../../static/tests/test_ui.py
[native/webview/main.c]: ../../native/webview/main.c
[ui/core/model/]: ../../ui/core/model/
[ui/core/search.js]: ../../ui/core/search.js
[ui/core/mount.js]: ../../ui/core/mount.js
[ui/core/nav.js]: ../../ui/core/nav.js
[ui/core/deeplink.js]: ../../ui/core/deeplink.js
[ui/core/model/deeplink.js]: ../../ui/core/model/deeplink.js
[ui/core/render.js]: ../../ui/core/render.js
[ui/core/renderers.js]: ../../ui/core/renderers.js
[ui/adapters/app-fsa.js]: ../../ui/adapters/app-fsa.js
[ui/adapters/app-http.js]: ../../ui/adapters/app-http.js
[ui/adapters/app-native.js]: ../../ui/adapters/app-native.js
[ui/adapters/http.js]: ../../ui/adapters/http.js
[ui/adapters/fsa.js]: ../../ui/adapters/fsa.js
[ui/adapters/preview-rich.js]: ../../ui/adapters/preview-rich.js
[ui/adapters/vfs-json.js]: ../../ui/adapters/vfs-json.js
[ui/adapters/vfs-csv.js]: ../../ui/adapters/vfs-csv.js
[ui/adapters/router-path.js]: ../../ui/adapters/router-path.js
[server/src/filemill/app.py]: ../../server/src/filemill/app.py
[server/src/filemill/api.py]: ../../server/src/filemill/api.py
[server/src/filemill/vfs.py]: ../../server/src/filemill/vfs.py
[server/src/filemill/preview.py]: ../../server/src/filemill/preview.py
[server/src/filemill/providers/sqlite.py]: ../../server/src/filemill/providers/sqlite.py
[server/src/filemill/providers/gitbundle.py]: ../../server/src/filemill/providers/gitbundle.py
[server/src/filemill/providers/vtt_provider.py]: ../../server/src/filemill/providers/vtt_provider.py
[server/tests/test_vtt_provider.py]: ../../server/tests/test_vtt_provider.py
[server/tests/test_vfs.py]: ../../server/tests/test_vfs.py
[server/tests/test_browser_keyboard.py]: ../../server/tests/test_browser_keyboard.py
[conftest.py]: ../../conftest.py

[the shared boot task]: ../tasks/152-centralize-the-shared-ui-boot-sequence.md
[The core initializer]: ../../ui/core/boot.js
