# Filemill architecture review and remediation plan

Reviewed 2026-09-19 at commit `bbcfc3b02b0a6e11bfb9b0f4b7a20b1eb6d2733a`.

Task `03497698-a9af-4637-9e93-9a25820853c4`, session `064c3896-dbfe-4b34-9bec-3c91375805a2`. Confirmed Astra Medium profile and Priority Kanban workflow. This deliverable is ready for user review. It authorizes no implementation, deployment, merge, or new tasks. The repository and tracker were left unchanged.

## Architecture and scope

Filemill is a small, local-first Miller-column file manager with two delivery modes and future native ambitions. The existing shared frontend is worth retaining. Most high-impact problems are broken contracts across its existing boundaries, rather than a need for a new framework or architecture.

The tracked repository contains 244 files, including 132 Markdown documents and 80 first-party Python, JavaScript, and CSS source/test files. The root `ui/` symlink points to `server/src/filemill/ui/`. The count includes 64 ADRs and 51 task documents. Generated `static/index.html` and vendored libraries are separate from the first-party source count.

| Area | Responsibilities and dependencies | Coverage |
| --- | --- | --- |
| Root guidance and product intent | `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `docs/GOALS.md` | Read; checked claims against implementation. Also read `static/AGENTS.md`. |
| Server entry/configuration | `cli.py:main`, `env.py:env`, `app.py:ROOT`, `_root`, `rt` | Traced CLI and ASGI startup, current/legacy environment names, route dispatch and application state. |
| HTTP and filesystem boundary | `app.py`, `paths.py`, `api.py`, `urls.py` | Traced listing, raw bytes, directory index, named mounts, representation URLs, save, delete, search, and virtual paths. Tested critical paths with temporary files. |
| Providers and server rendering | `vfs.py`, `providers/{sqlite,json_provider,vtt_provider}.py`, `preview.py` | Read registration/classification and provider behavior; tested SQLite identity and WITHOUT ROWID. Inspected bounded-text and docutils settings. |
| Browser application | `entry-static.js`, `entry-server.js`, `core/{ports,state,mount,nav,deeplink,render,layout,sort,typeahead,search,settings,shell,trail,syntax,icons,dom,debug,limits,file-kind}` and CSS | Reviewed module boundaries, selection/focus, asynchronous loads, caching, layout, keyboard/touch, rendering and URLs. Focused browser checks used modular sources. |
| Adapters and editor | All HTTP/FSA, router, storage, boot, virtual-file and preview adapters; five editor modules | Traced mount/restore, source changes, render routing, edit/save/delete and permissions. Tested representative adapter failures. |
| Tests and build | Root fixtures/config, all 16 server test modules, static UI/URL/rich/PWA/E2E suites, build script, RST measurement script, Deno/pre-commit/uv configuration | Inspected test inventory and fixtures; ran non-browser server tests and focused browser probes. Reviewed browser suites and manual checks without running the full interactive suites. |
| Delivery and dependencies | GitHub workflow, package metadata/lock, bundled HTML, manifests, both service workers, vendor inventory | Checked bundle freshness, vendor hashes, module packaging intent, cache behavior, and CI command paths. No live deployment or wheel-install smoke test. |
| Design and backlog | `TASKS.md`, all task-document scopes/status/dependencies, previous review, roadmap, ADR catalog and relevant decision details | Mapped overlap and contradictions. Historical completion records are evidence of earlier work, not proof of current behavior. No tracker maintenance performed. |

### Runtime map

-   The static edition starts at `static/index-dev.html` → `entry-static.js` → shared shell/core → `app-fsa.js`. It asks the browser for a directory handle, wraps FSA with JSON/JSONL/CSV adapters, mounts nodes, then restores a hash URL or remembered selection. `build-index.py` concatenates this module graph and inlines CSS/icons/font into the committed HTML. PWA installation additionally needs the manifest, worker and icons published by CI.
-   The server starts at `filemill.cli:entry_point` → Typer `main` → Uvicorn → the Starlette app. `app.py:rt` adapts query/path arguments and sends synchronous handlers to the thread pool. `_root()` chooses `app.state.root` or the import-time environment root. CLI startup writes app state; direct ASGI startup uses the environment fallback. CLI and direct-ASGI root defaults differ.
-   The server emits a shared shell with configuration attributes, hashed asset URLs and an import map. `/api/dir` supplies nodes and metadata through HTTP; the same core handles navigation. Raw files use `/api/raw`, root-relative resource URLs, or `/w/` named mounts. `/n/` remains an alternate shell prefix. Bare directory URLs can serve `index.html`; bare file URLs serve bytes.
-   Browser previews mostly consume `FS.blob`. Markdown and DOCX use vendored modules on the server and pinned CDN modules in the static edition. Static RST uses pinned Pyodide/docutils; served RST uses `/api/preview`. Current PPTX code is a local ZIP/XML text extractor, despite documentation claiming a CDN slide viewer. SQLite is server-only JSON data. JSON/JSONL/CSV trees are browser adapters.
-   `state.js` owns mutable path, selection, focus, fold and preview state. `nav.js` changes it; `render.js` reconciles cached columns; layout computes folding/panning; `deeplink.js` synchronizes router state. This is a DOM-coupled singleton application. The FS/PREVIEW/ROUTER seams are useful but incomplete: `HTTP.loadPage` mutates core state and renders, and core search knows `/api/search` directly.
-   Text editing uses `editableText` → textarea/undo/find/gutter → `FS.write`. FSA requests write permission when needed; HTTP posts bytes. Delete uses the optional `FS.remove` port. Server mutations have no authentication or request-origin validation. Files are the durable data; there is no application database on the server. SQLite files are opened read-only.
-   Browser persistence is IndexedDB `filemill/kv/recent` for up to eight handles plus view chains, localStorage for settings, history for navigation, and Cache Storage for service workers. There is no durable edit draft, server session store, or filesystem watcher. Refresh is explicit.
-   Integrations are filesystem handles, browser storage/history/clipboard/fullscreen APIs, ripgrep subprocess search, SQLite, docutils/Pygments, pinned browser renderers, Uvicorn and GitHub Pages. Server deployment/service/proxy settings live outside this checkout. Loopback is the CLI bind default; a remotely reachable deployment needs external access control under the documented trusted-user model. No installed-PWA mechanism starts the Python service.

### Critical paths examined

1.  Directory selection → `choose` → wrapped `ensureLoaded` → `/api/dir` or FSA entries → classification/order → column cache → preview → URL write.
2.  Deep-link reload → server path validation → shell → router read → `applyPath` → name lookup in loaded children. Pagination breaks this path beyond page one.
3.  Markdown/file preview → byte acquisition → registry/decorator selection → HTML string → `fillPreview` innerHTML. The wikilink rule can turn escaped text back into executable markup.
4.  Edit → text validation → save request → root resolution → direct overwrite → metadata → refreshed preview. No optimistic concurrency or atomic replacement exists.
5.  Delete confirmation → FSA/HTTP remove → filesystem mutation → selection/list update. Both the local adapter and success callback contain defects.
6.  Directory URL → safe directory resolution → implicit `index.html` response. The appended file bypasses the containment check.
7.  PWA request → broad cache lookup → stale response/background fetch. Raw file bytes are cached; the offline miss does not return a Response.
8.  Search input → fixed-string ripgrep subprocess → captured JSON output → first 100 match events → navigation. The cap is applied after the subprocess has produced all output.

## Verification and evidence limits

Checks used the existing Python environment at `/home/agent/prg/filemill/server/.venv` with `PYTHONPATH` pointing to this checkout. Starlette 0.52.1, Uvicorn 0.41.0, Playwright 1.61.0, docutils 0.23, Pygments 2.19.2, Typer 0.24.1 and pytest 9.0.2 matched the reviewed lock. The borrowed environment also contains python-pptx, which is not declared by this checkout. A fresh offline dependency install was unavailable; its unused environment was removed. Sandbox-blocked browser/TestClient work was rerun with approved local execution. No packages or browsers were downloaded.

-   Root-configured server checks completed: `python -m pytest -c pytest.ini -q -p no:cacheprovider -m 'not integration' server/tests` reported **334 passed, 222 failed, 118 deselected**. This is a mixed product/test-infrastructure result, not 222 independent product defects. A separate safety test failed in isolation. Logs: `/tmp/filemill-review-root-tests.log`, `/tmp/filemill-review-safety-isolated.log`.
-   A first run using server configuration showed missing-fixture errors and was stopped. The documented `cd server && ... pytest` selects the nested configuration; shared fixtures now live above that root.
-   `python3 static/build-index.py --check` failed. An in-memory rebuild comparison showed differences in history logic, column-width stabilization and PPTX text extraction. The tracked bundle was not rewritten.
-   Direct execution of `static/test-ui.py`, `test-url.py`, and `test-rich.py` exited successfully without running their test functions. They now expose pytest wrappers but have no standalone entry call. Their wrappers still call `sys.exit`, including on success.
-   Ruff check passed. Ruff format reported seven files needing formatting. Mypy reported two argument-type errors at `api.py:173`. Non-vendor Deno lint passed for 38 files. Full Deno formatting emitted differences and was stopped after exceeding a useful bounded run; no full formatter pass is claimed.
-   Isolated HTTP fixtures reproduced a nested index symlink escape, a cross-origin save accepted with HTTP 200, and invalid `page=bad` returning HTTP 500.
-   Isolated Chromium checks reproduced Markdown script execution, HTML-preview parent access, FSA deletion refusal, a successful mocked deletion followed by a failure message, oversized-image rejection, preview rebuilding on unchanged render, page-two deep-link failure, missed page-two JSON adaptation, and ignored descending name sort.
-   SQLite fixtures reproduced duplicate navigation keys for distinct long primary keys and an empty result for a populated WITHOUT ROWID table.
-   A Node VM exercised each actual service-worker fetch handler with controlled cache/fetch implementations. Both cached a raw document URL; an uncached offline request resolved to `null`. This verifies handler logic, not every installed-browser lifecycle.
-   Vendor module hashes inspected matched the documented renderer hashes. Vendored third-party implementations were not audited line by line or checked against current vulnerability databases.

Browser reproduction scripts are `/tmp/filemill-review-browser.py` and `/tmp/filemill-review-paging.py`; worker reproduction is `/tmp/filemill-review-sw.cjs`. These are review scratch files, not committed tests. They use temporary or in-memory data. No public demo, private user file, deployed service, or real user directory was mutated. Full browser/mobile/real-picker suites, cold CDN timing, installed-PWA upgrade, clean wheel installation, and production proxy behavior remain unverified. Historical performance numbers in ADRs were not remeasured.

## Prioritized findings

P1 means fix before relying on the current build for ordinary writable use or expanding exposure. P2 means the next reliability/correctness tranche. Likelihood is conditional on the described trigger, not a claim about observed production incidents. Effort is a planning estimate: S is up to roughly one day, M is one to three days, L is several days. Change risk describes implementation risk.

| Rank / ID | Finding | Impact and likelihood | Effort / change risk | Plan dependencies |
| --- | --- | --- | --- | --- |
| 1 / F1, P1 | Implicit index bypasses path containment | Outside-root disclosure; certain with an escaping nested index symlink | S / low | Focused regression gate |
| 2 / F2, P1 | Preview content can execute as Filemill | Read/write access within existing app grants; confirmed for crafted Markdown and HTML | M / medium | Tests; coordinate F3 |
| 3 / F3, P1 | Mutation endpoints accept unrelated origins | Unwanted overwrite if another page can reach server; endpoint acceptance confirmed, browser reachability varies | M / medium | Explicit mutation contract |
| 4 / F4, P1 | Test and delivery gates do not verify advertised behavior | Broad regression escape; present on every current CI invocation | M / low-medium | First enabling step |
| 5 / F5, P1 risk | Saves lack atomicity and conflict detection | Partial/lost data on failed or competing writes; implementation risk confirmed, incident not reproduced | M / medium | F1/F3; write semantics |
| 6 / F6, P1 | Service worker caches raw files and breaks offline misses | Stale/private bytes retained; recovery failures; certain for matching requests | M / medium | Upgrade/cache migration tests |
| 7 / F7, P1 | Delete fails locally or reports failure after success | Core operation unusable or misleading after irreversible action; deterministic | S-M / low-medium | F4; mutation safety tests |
| 8 / F8, P2 | Pagination does not compose with navigation/virtual adapters | Page-two files fail restoration or lose structured browsing; deterministic above 500 entries | M / medium | Shared listing/address contract |
| 9 / F9, P2 | SQLite identity and errors lose accessible data | Distinct rows collapse; valid tables look empty; deterministic for affected schemas | M / medium | F8 address decisions |
| 10 / F10, P2 | Preview routing and limits disagree across modes | Normal media rejected, local RST calls wrong source, controls misrepresent mode | M / medium | F2; existing preview tasks |
| 11 / F11, P2 | Preview lifecycle rebuilds and lacks unified navigation ownership | Repeated reads, reset media/scroll, stale asynchronous work; rebuild reproduced | M / medium | F10; existing cache/history tasks |
| 12 / F12, P2 risk | Resource limits apply after expensive work | Memory/latency spikes on ordinary large files/trees; structural evidence, no load benchmark | M / medium | F5/F8/F10 |
| 13 / F13, P2 | Current guidance contradicts implementation | Wrong setup, threat and feature expectations; widespread and confirmed | M / low | Correct alongside each fix; final pass |

### F1. The directory index is served without validating its resolved target

Evidence: `server/src/filemill/app.py:395-397`, `resource`; `paths.py:26`, `resolve_safe`. The requested directory passes `_resource_target`, then `target / "index.html"` is sent directly through FileResponse. With a temporary `root/sub/index.html` symlink to an outside file, `/sub/index.html` returned 404 while `/sub/` returned 200 and the outside bytes. This is a confirmed bypass of the documented nested-symlink boundary, distinct from deliberately allowed direct-root bookmark symlinks.

No matching dedicated backlog item was found. It is adjacent to the completed path extraction task \[24\] and the earlier review's security section. The fix should also audit appended children and avoid claiming race-free containment: current resolve-then-open operations still assume the trusted local filesystem is not being adversarially swapped between validation and use.

### F2. The Markdown wikilink rule disables escaping for surrounding text

Evidence: `ui/adapters/preview-rich.js:192-205`, `markdown`; `ui/core/render.js:609`, `fillPreview`. The rule changes an entire text token to `html_inline` and only escapes the matched link's target/label. Other characters in that token become raw HTML. A local browser probe rendered an image event handler beside `[[note]]` and observed its harmless test marker execute in the parent page, despite markdown-it being configured with `html: false`.

Related boundary: `ui/core/renderers.js`, HTML renderer around line 172, creates an unsandboxed blob iframe. A harmless HTML fixture set a property on its parent. Both entry modules publish FS and state through `core/debug.js:exposeCore`; executing content shares app authority. Removing debug globals alone would not establish a boundary. Server raw HTML and `/w/` intentionally share the app origin as well. `preview-rich.js:docxHTML` inserts converter HTML without a separate sanitizer; this is an audit target, not a separately reproduced DOCX exploit.

`SECURITY.md` requires trusted files and users, which reduces the assumed attacker population. It does not make unexpected Markdown execution consistent with `html: false`, or establish a safe preview boundary for granted local folders. The previous review already noted same-origin HTML calling save. No claim of observed exploitation is made. External images in rendered content also invalidate the blanket claim that renderer downloads are the only possible network access.

### F3. Loopback and absence of CORS headers do not authorize writes

Evidence: `app.py:28`, app construction without origin/host mutation middleware; `app.py:296-302`, `api_save`; `app.py:305-315`, delete; `ui/adapters/http.js:write`. A POST with unrelated Origin and `text/plain` content overwrote a disposable file and returned 200. There is no token or Origin check. CORS read restrictions do not themselves reject such a write request. A full hostile-origin browser scenario depends on browser local-network restrictions and deployment topology and was not exercised; the endpoint behavior is confirmed.

`SECURITY.md:Named mounts` and CHANGELOG describe removal of CORS as if it established same-origin-only access. They should distinguish readable responses, navigation, script execution and mutation authorization. Host/DNS-rebinding resistance also needs an explicit local-server policy. Preserve the intended trusted remote/reverse-proxy use through configured allowed origins/hosts rather than assuming every deployment is loopback.

### F4. The quality gate has both false-green and persistent-red paths

Evidence: `.github/workflows/publish.yml`, “Test the bundle and the shared sources”, calls the static scripts directly. `static/test-ui.py:2201`, `test-url.py:286`, `test-rich.py:489` define pytest wrappers only. Direct calls did nothing and exited zero. Their `main` functions end in `sys.exit(0)` on success, which is unsuitable as a passing pytest test. Root `pytest.ini` also collects `test-*.py`, while `static/test-e2e.py:372` runs the manual headed suite at import time.

The documented server command uses `server/pyproject.toml` test configuration, while fixtures were moved to root `conftest.py`. Even using the root configuration, the complete non-browser run is red. Specific infrastructure causes include `test_cli.py:test_main_default_root_uses_cwd` asserting old module-global configuration while CLI now changes `app.state.root`, and leaving that state behind; other tests still patch `ROOT`. `test_resource_safety.py:recorder` wraps `resolve_safe` with a two-argument spy while `app.py:_resolve` passes three, producing 500s in the safety matrix. There are also stale expectations and genuine failures, so blanket deletion or xfail would conceal useful coverage.

`server/tests/test_browser_new_ui.py:ui_root` imports python-pptx, absent from the declared dev dependencies/lock. The borrowed review environment masks that clean-install problem. Bundle freshness, Python formatting and mypy fail as described above. Vendor files are included in broad Deno checks; prior task \[28\] records the resulting lint/formatting burden.

Overlap: \[25\] is still In Progress; \[12\] and shared-fixture consolidation are marked Completed; \[43\] records an older, explicitly unverified count of 11 browser failures. This review does not replace \[43\]'s history with the new non-browser count. Reuse those scopes and record new dated evidence.

### F5. A failed or stale save can lose file contents

Evidence: `api.py:312-329`, `save_file`, validates then calls `target.write_bytes(data)` directly. Opening for overwrite truncates the file before the write completes; catching OSError reports failure but cannot restore prior bytes. HTTP reads/writes carry no revision precondition, so a second tab or external editor's change can be overwritten silently. `editor/editor.js:save.onclick` sends only current text; the modified indicator is not a conflict detector. This is an architectural data-integrity risk, not a reproduced disk-failure incident.

`app.py:302` buffers the complete request before the size check. `preview.py:read_text` reads complete old bytes before checking text size. The async save handler then performs synchronous filesystem I/O on the event loop. FSA uses browser writable streams, but still has no external-change check and no explicit abort on failed writes.

Task \[28\] explicitly preserves navigation's discard behavior. Do not relabel that deliberate scope decision as an accidental regression or silently add autosave. Disk-write integrity and external-change detection are separate gaps.

### F6. The service workers retain document bytes and return an invalid offline result

Evidence: `server/src/filemill/static/sw.js:49-78` and `static/sw.js:49-78`. Every same-origin GET outside the API exclusion takes the same cache-first path. Root-relative raw files and `/w/` are therefore cached despite `/api/raw` being excluded. A cached response wins even while a fresh response is fetched, so the first revisit after save/delete can show stale bytes. Cache Storage receives explicit `put` calls even for resource responses carrying `Cache-Control: no-store`.

`return cached || networkFetch || new Response(...)` tests the Promise itself. On a miss and failed fetch, that Promise resolves to `null`; the fallback Response is never selected. Both behaviors were reproduced against the actual worker handlers in a VM. Both use the static cache name `filemill-v1`; activation deletes all other origin cache names, not just this app's obsolete caches. Background cache writes are not explicitly attached to fetch-event lifetime.

Overlap: static PWA addition and \[36\] are completed. ADR 0063 promises server-unavailable recovery, but uncached navigation cannot reliably reach it. Root precaching can also capture a user's `index.html` rather than the Filemill shell. Fix both editions and test installed upgrades, not only worker-source substrings.

### F7. Delete crosses the filesystem boundary but fails at both UI seams

Evidence: `ui/adapters/fsa.js: fsaNode` stores the directory handle in `node.parent`; `FSA.remove` checks and calls `node.handle.parent`, which a real FSA handle does not supply. The probe with a valid node parent returned “Cannot delete this entry”.

`ui/core/render.js:549-553` calls `actions.render()` after successful removal. Boot modules pass `choose`, `refreshColumn`, `renderCrumbs`, `saySt`, and `unfoldTo`, but not render. The probe completed a mocked deletion then displayed “Delete failed: actions.render is not a function”. A real server delete can therefore have already destroyed the file when the UI claims failure. In addition, `render:326` wires actions only for `previewNode()`, leaving the directory-only selected-state toolbar without that setup.

The generic delete feature is marked Completed in TASKS.md. These are current regressions against that feature, not a new delete design. Keep existing confirmation and root/symlink protections; use disposable data for all verification.

### F8. A page of nodes is treated as a complete navigable directory

Evidence: `api.py:134-188` slices listings at 500 entries; `ui/adapters/http.js:ensureLoaded` loads page one; `ui/core/deeplink.js:applyPath` only searches `visibleKids(parent)` and has no lookup/load-other-page path. A mocked 501-entry directory failed to restore a valid page-two name. This also affects refresh and remembered selections.

`HTTP.loadPage` duplicates entry construction, writes node children directly, truncates global navigation state and renders. The JSON/CSV wrappers only decorate children after `ensureLoaded`, so page-two `z.json` remained a non-virtual file in the browser probe. Size/date sorting and type-ahead operate only on the loaded page. `dir_json` rescans/stats/sorts the entire directory for each page, so pagination bounds response size but not server work.

Related identity issues are hidden by name-based paths: RouterHash first decodes URLSearchParams then calls `decodeURIComponent` per segment, which needs percent/slash round-trip tests. Core dotfile filtering applies to virtual JSON keys as well as filenames. These are further contract checks, not all independently reproduced failures. No dedicated pagination task was found; \[7\], \[22\], \[39\], \[45\], and \[61\] are relevant adjacent contracts.

### F9. SQLite labels double as identifiers and legitimate errors become emptiness

Evidence: `providers/sqlite.py:118`, table labels are truncated; `:145-150` and `:_row_key` truncate row keys before constructing vpaths. `core/state.js:rowIndex` and `deeplink.js:applyPath` select by name. Two distinct text primary keys sharing their first 59 characters produced the same name and vpath. Such rows cannot remain independently addressable through the current selection model.

`sqlite.py:139` always selects rowid. A populated WITHOUT ROWID table returned no entries because `list_entries` catches every exception and returns `[]`. Missing/corrupt/unsupported data therefore looks like an empty table. `_row_key` also runs schema and uniqueness queries per row, although these are table-level facts; the repeated work is confirmed structurally, but its production latency was not measured. URI construction should also be tested with `?` and `#` in database filenames.

Overlap: \[34\] delivered JSON rows; \[61\] solved a similar CSV-label problem. Reuse the identity principle without reopening the closed speculative ViewSpec task \[9\]. This is not a request for an ORM or general database explorer.

### F10. Renderer selection is split across registry, decorators, metadata and toolbar state

Evidence: `ui/adapters/preview-local.js:render` rejects any metadata size above TEXT\_MAX before looking at kind. The probe rejected a 524,289-byte PNG. Ordinary photos, PDFs and videos exceed that text limit. Meanwhile rich previews can fetch complete bytes before checking text size.

`ui/adapters/app-http.js:119-126` sends every non-virtual RST node to PreviewHTTP. Its local-folder mount uses the same wrapper at `:mount`; local nodes lack `rel`, so this path requests `/api/preview?p=undefined` instead of the browser's RST renderer. The server registry setup also excludes RST. This is a traced routing defect, not a fresh reproduction of every reported RST symptom.

`render.js:442-450` writes preview view with no root argument, while RouterHash expects one; static PreviewRich has no general highlighted-source dispatch. The Raw toolbar URL is always a server-style root-relative URL whenever any router exists, including the static hash router. The server local-folder mode has a null router, so setPreviewView returns before changing mode. Representation should be an explicit preview/router contract instead of a truthiness test for ROUTER.

Overlap: preserve \[41\] as the current RST regression, separate from completed \[27\]/\[50\]; preserve \[38\] for PPTX fidelity, \[10\]/\[56\]/\[63\] for toolbar/mode contracts, and \[42\] for the separate home-link defect. `preview-rich.js:localHref` also drops relative-link query/fragment suffixes; fix that alongside \[42\] only with its original acceptance behavior retained. Do not declare those tasks resolved from source inspection alone.

### F11. Only active editing survives an unchanged render

Evidence: `render.js:319`, `renderPreview:345-402`, and `fillPreview:573`. Outside editing, every render creates a new preview element, revokes its object URL and calls the preview provider again. The browser probe observed one extra provider call and a different element for a render with unchanged selection. Resize and other renders can therefore repeat HTTP reads/parsing, reset media and scroll, and destroy fullscreen/focus continuity. A stale-result token prevents many wrong fills but does not cancel expensive work or give each asynchronous renderer its own resource cleanup.

`nav.js:choose` and refresh use `navSeq`; `deeplink.js:applyPath` has only a shared boolean and mutates global path across awaits. Rapid overlapping history/mount operations are a race risk needing delayed-load tests. Do not claim a particular race was reproduced here. The single global object URL in `renderers.js` deserves the same stale-completion checks.

Overlap: \[21\] is marked Completed but its cache is absent in current source. \[29\] depends on \[21\], so its prerequisite is not currently satisfied. \[39\], \[40\], \[64\] remain open; \[48\]/\[52\] are earlier completed fixes. Reuse those invariants. Native extraction should wait until the ordinary browser lifecycle is stable.

### F12. Several “bounded” paths bound the result rather than the work

Evidence: `api.py:49-115`, `search_root`, uses `subprocess.run(capture_output=True)` and only stops parsing at 100 matches after the full process finishes. `--max-count 1` is per file. Large trees and long matching lines can still generate substantial captured JSON and consume the full timeout. Client AbortController does not cancel the server subprocess. No heavy benchmark was run, so the frequency/size threshold is unknown.

Other examples: `preview.py:read_text` and `_preview_rst` read complete files; JSON loading in `vfs-json.js` checks blob size after fetch, unlike JSONL/CSV metadata prechecks; PPTX extraction and DOCX conversion have no archive expansion limit; directory paging repeats full enumeration; FSA metadata sweeps use unbounded Promise.all. Existing 3,000-entry measurements support retaining the current design at that scale, not a claim that every resource path is bounded.

Overlap: \[49\] and \[60\] cover search history. Raising the timeout does not implement a global output/work limit. The separate open task for search-result preview navigation remains valid, since `core/search.js` assigns a bare resource URL.

### F13. Documentation records useful history but presents incompatible current contracts

Concrete examples:

-   `README.md` and `server/README.md` claim a CDN PPTX viewer; `preview-rich.js:unzipPptx/pptxHTML` implements local text extraction.
-   `server/CONTRIBUTING.md` describes removed `rendering.py`, `/api/render`, `preview-upload.js`, old wheel exclusions, and a no-file-data caching guarantee contradicted by F6. Its claimed 100% branch coverage is not enforced by the workflow.
-   `static/AGENTS.md` lists removed adapters and initially describes a read-only/no-network app, while FSA supports write/remove and rich renderers are default-on. ADR 0034 says nothing writes; ADR 0005 specifies node.lastSel, removed by the completed selection-model task.
-   ADR 0001 still describes upload rendering; ADR 0002's server-rendering claim needs a dated supersession note. ADR 0064 is valuable measured history, but its standalone focused commands currently hit the no-op paths in F4.
-   `docs/ROADMAP.md` still instructs deletion of already-removed HTMX modules and adding tools that now exist. `docs/ARCHITECTURE-REVIEW.md` is explicitly dated 2026-09-05, so its counts are historical, not fresh failures. The roadmap should not present that snapshot as a current ordered execution plan.
-   CLI README environment promises do not match `cli.main`: ROOT falls back to cwd despite FILEMILL\_ROOT being used for direct ASGI import, and FILEMILL\_LIVE is written for reload but not read to select CLI live mode.
-   The changelog's CORS statement is too broad; the security document needs write/delete authority and browser cache/content-origin behavior, not just read exposure.

TASKS.md has duplicate placements for \[38\], \[39\], \[40\], and \[42\] across Scheduled/In Progress, and a loopback-default item still In Progress although code/default docs already show loopback. These are handoff observations for the earlier tracker-maintenance work, not permission to move them. Task descriptions explicitly preserve later regressions independently of earlier completed work. Retain those distinctions.

## Ordered remediation plan

These are proposed implementation steps for later authorization. Each should be a bounded, reviewable change with its own regression checks and documentation. Security fixes can use focused tests immediately; do not postpone them until every historical test is green. Do not weaken checks merely to make the gate pass.

### 1\. Make the verification path execute real tests, then establish the baseline

Addresses F4; enables every later step. Reuse \[25\], \[12\] and \[43\] rather than starting another test-harness plan.

-   Choose one documented root pytest invocation and explicitly pass its configuration in CI. Keep headless static tests in collection, but exclude the manual headed E2E script and remove import-time execution. Convert success from SystemExit to normal return/assertions; make --dev and focused options genuine pytest options or restore intentionally supported standalone entry points.
-   Repair fixtures to use one root configuration mechanism, restoring app state after each test. Update the path-safety spies for the zones parameter. Use a test app factory only if app-state restoration is insufficient; a larger application rewrite is unnecessary.
-   Declare python-pptx as a test-only dependency or replace those test fixtures with a checked-in/generated fixture that uses declared dependencies. Keep all runtime dependencies justified.
-   Rebuild the generated HTML in the later implementation change, run its freshness check, and align CI/documented commands. Keep vendor format/lint policy explicit; check first-party files without rewriting minified vendor code. Fix the two mypy errors and formatting baseline in distinct mechanical changes.
-   Acceptance: a deliberately failing assertion makes each advertised command and CI job fail; both static modes report actual collected/passed tests; the manual picker does not run at collection; random ordering cannot leak root state; safety tests execute real resolution. Establish an exact named failure list and fix stale expectations without deleting behavior coverage. End the remediation series with all selected gates green.
-   Verification: clean locked environment, root test collection, bundle/dev smoke, safety matrix, then full headless suites. Documentation: root/server contribution guides, static guide, \[25\]/\[43\] dated results.
-   Migration/rollback: no user-data migration. Keep command compatibility where documented, or publish the exact replacement. Roll back test-runner wiring independently of product fixes; never restore a false-green command as the accepted gate.

### 2\. Close path escape and authorize mutations at the HTTP boundary

Addresses F1/F3. Depends only on focused working tests from step 1.

-   In `app.py:resource`, validate the final index file with the same request zones used for explicit resource resolution. Audit other derived-file responses and keep direct-root bookmark behavior explicit in `paths.py` and SECURITY.md.
-   Define a small mutation policy for save/delete: validate configured host/origin, reject unrelated browser origins, and require a per-instance/session mutation token or equivalent explicit same-origin authorization. Validate before reading the body. Document supported non-browser clients and reverse-proxy origin configuration. Keep default bind loopback.
-   Acceptance: escaping nested index returns the same denial as its explicit URL; valid in-root indexes and intentional bookmarks work; unrelated-origin POST cannot change fixture bytes; missing/invalid authorization cannot delete; legitimate UI writes through configured local/proxy origins pass.
-   Verification: temporary symlink matrix across resource/raw/index/mount routes; browser request tests with two loopback origins; host/origin and body-stream rejection tests. Correct SECURITY.md/CHANGELOG CORS wording and CLI deployment guidance.
-   Migration/rollback: mutation authorization changes the client/server API, so ship matching UI and server changes together and document proxy/client settings. No filesystem migration. If compatibility fails, disable mutations while repairing configuration instead of reopening unrestricted writes. Resolve/open TOCTOU hardening remains a separately scoped decision under the trusted-filesystem assumption.

### 3\. Establish a safe preview-content boundary

Addresses F2. Coordinate with step 2; neither protection substitutes for the other.

-   Rewrite wikilinks as proper inline text/link tokens, or escape all untouched text spans before constructing HTML. Cover malformed/incomplete wikilinks as well as valid matches.
-   Sandbox HTML previews without same-origin script authority. For intentional raw website hosting, separate the content origin or apply a response sandbox policy appropriate to that mode; do not silently break the documented bare-HTML web-server behavior. Choose and document the smallest compatible option.
-   Audit DOCX output and URL-bearing fields, including .desktop links, through an explicit sanitizer/safe-protocol policy. Constrain remote resource loading according to the promised privacy behavior; distinguish renderer downloads from embedded images and scripts. Avoid adding a broad security framework.
-   Acceptance: crafted Markdown remains inert with and without wikilinks; legitimate links, code, footnotes and formatting still work; preview HTML cannot reach parent FS/storage or mutation endpoints; unsafe URLs do not execute; any intentionally active raw website mode has an explicit boundary and documentation.
-   Verification: both editions, vendored/stubbed rich modules, browser parent-access and harmless-script-marker tests, remote-request interception. Update SECURITY.md, preview adapter docs and relevant ADR supersession notes.
-   Migration/rollback: some formerly active previews may lose scripts or same-origin resources. Preserve a clearly documented deliberate web-hosting route if needed. Roll back visual regressions separately; retain escaping and sandbox protections.

### 4\. Make save and delete outcomes reliable

Addresses F5/F7; depends on step 2 and tests from step 1.

-   Implement a bounded server write path with atomic replacement using a temporary file in the same directory, explicit cleanup, and appropriate flush/durability behavior. Preserve required permissions and define symlink/hard-link behavior before replacement; resolve intended symlink targets without replacing bookmark links accidentally.
-   Carry a revision from read through save and reject stale writes with a conflict response. Keep the edited text visible for resolution. For FSA, recheck the file before writing and abort an unfinished writable stream on failure where supported.
-   Fix `FSA.remove` to use the stored parent handle and appropriate permission context. Fix the missing render callback or call the local renderer directly. Wire selected-directory actions explicitly, retain confirmation, and distinguish backend success from subsequent display-refresh errors.
-   Acceptance: simulated write failure leaves old bytes intact; concurrent edit is rejected without losing the draft; successful save reloads exact text; cancel and read-only behavior remain unchanged. File, directory and symlink deletion work in disposable trees; root deletion remains denied; successful deletion never reports “Delete failed” merely because rendering failed.
-   Verification: injected write/replace/permission failures, two-editor conflict tests, real OPFS parent-child remove tests, HTTP delete tests and browser success/error states. Update editor task \[28\] with separate integrity behavior and the existing delete completion with dated regression evidence, coordinated with tracker ownership.
-   Migration/rollback: no bulk file migration. Revision preconditions require matching UI/API changes. Document atomic-replace effects on hard links, ownership and watchers. There is no promise of trash/recovery; retain the explicit permanent-delete confirmation. Keep a read-only fallback if mutation correctness is uncertain.

### 5\. Restrict PWA caches to application assets and migrate existing caches

Addresses F6; requires browser lifecycle checks from step 1.

-   Use an explicit asset/shell cache policy. Keep document/raw/mount responses network-only and preserve normal response semantics. Precache a known Filemill shell route, not arbitrary user index content. Await network failure before selecting a real offline/recovery Response.
-   Attach background update work to event lifetime, version Filemill cache names, and delete only this app's obsolete caches. Plan removal of legacy `filemill-v1` entries that may contain private bytes. Apply equivalent rules to both workers without unnecessary cache infrastructure.
-   Acceptance: viewing or downloading a file adds no document bytes to Cache Storage; save/delete is reflected on the next read; unrelated caches survive activation; a cold offline navigation produces a valid recovery page; an installed app with previously cached shell reconnects when the server returns.
-   Verification: browser worker install/control/update tests, warm and cold offline navigation, root with index.html, renamed/deleted files, and old-cache migration. Replace source-substring-only assurances with request/cache assertions. Update PWA docs and ADR 0063.
-   Migration/rollback: bump worker cache version and explicitly purge legacy document caches. Verify upgrade on an existing installation; do not advise clearing all site storage, which would discard remembered folder handles. A rollback worker must retain network-only document behavior and a valid offline response.

### 6\. Make navigation independent of the current listing page

Addresses F8; coordinates with \[7\], \[22\], \[39\], \[45\] and \[61\].

-   Define whether a directory operation addresses the full logical directory or a displayed page. Add a focused adapter child-lookup/seek mechanism for deep-link restoration, or deliberately load the complete listing where current scale supports it. Do not simply scan every page for every keystroke.
-   Use one HTTP entry-construction/adaptation path for initial load and later pages. Keep state changes/rendering in the navigator rather than inside the transport. Reapply JSON/JSONL/CSV wrappers to every page.
-   Decide and label sorting/type-ahead scope. If the UI promises directory-wide sorting, implement it at the listing source before paging. Preserve stable selection across refresh and page changes. Round-trip percent signs, slashes in virtual keys, Unicode, empty keys and hidden-data keys without applying filesystem-only filtering to records.
-   Acceptance: first/last/page-two files and structured files reload and restore correctly in a 1,001-entry fixture; refresh retains a still-existing selection; size/date/name order matches the stated scope; virtual records do not disappear because of adapter bypass.
-   Verification: API pagination contract plus browser navigation/refresh/Back/Forward, bundled and modular builds, FSA parity for non-paged directories. Document the contract in ports.js and adapter README.
-   Migration/rollback: preserve existing ordinary path URLs. If virtual IDs change, provide deterministic legacy resolution where possible and a visible unavailable-path outcome otherwise. No disk migration; browser remembered view records may need versioned interpretation.

### 7\. Separate SQLite identity from display text

Addresses F9; use the address contract from step 6.

-   Keep full stable table/row IDs separate from truncated display labels. Encode path segments unambiguously and handle composite keys and duplicate-looking labels. Keep truncation strictly presentational.
-   Support WITHOUT ROWID tables using primary-key identity, or report a clear unsupported-schema error instead of an empty list. Distinguish empty, inaccessible, corrupt and unsupported results in the provider/API.
-   Compute table metadata and candidate-key uniqueness once per listing, not once per row. Retain read-only SQLite connections and quoted identifiers. Test URI-special filenames and clear row-limit reporting; do not add an ORM.
-   Acceptance: colliding long labels remain independently selectable and reloadable; populated WITHOUT ROWID tables are readable or explicitly unsupported; bad databases show errors; no write-capable connection is introduced.
-   Verification: long/composite/null/blob key fixtures, quoted/slashed table names, two distinct rows with identical display prefixes, statement-count assertions and browser selection. Update SQLite/port documentation and cross-reference \[34\]/\[61\].
-   Migration/rollback: old virtual URLs may require compatibility lookup. Files themselves are unchanged. Retain explicit failure if old truncated IDs are ambiguous; do not guess a row.

### 8\. Unify preview capability and representation decisions

Addresses F10 and part of F12. Depends on the preview trust boundary from step 3.

-   Keep the registry, but give it an explicit representation and source capability contract. Use the browser RST renderer for browser-granted files, and the server renderer only for server-owned paths. Ensure Source/Rendered works when routing is disabled.
-   Apply text limits only to text. Define separate sensible media/office limits; serve HTTP media through direct/range-capable URLs when appropriate rather than always buffering blobs. Reject oversized text before fetching, with a post-read guard too.
-   Make Raw an adapter capability: static files need object URLs/downloads, server files need canonical resource URLs, and virtual records need their own representation. Preserve root and mode through the relevant router. Remove the duplicate competing Markdown mode controls only after specifying their intended distinction.
-   Acceptance: a normal image/PDF/video above 512 KiB previews; large text is declined without a full HTTP download; local-folder RST makes no `/api/preview?p=undefined` request; Source/Rendered/Raw have consistent documented behavior in static, served, local-folder and virtual modes.
-   Verification: a compact matrix across file kind, source, representation, online/offline and consent state; test actual output and requests, not just button labels. Extend existing \[41\], \[38\], \[42\], \[10\], \[56\], \[63\] scopes without merging their distinct bug reports. Correct README/PPTX/RST statements to the shipped implementation.
-   Migration/rollback: maintain existing server resource URL contract and raw hosting use. Regenerate the static bundle. If a rich renderer fails, fall back to safe source or an explicit unavailable preview, not an incorrect renderer or data upload.

### 9\. Restore preview identity and give asynchronous navigation one owner

Addresses F11; repairs the prerequisite for \[29\]. Follow step 8's explicit representation key.

-   Reuse the preview element for the same node, revision, representation and relevant settings; invalidate on save/refresh/mode change. Preserve the active editor behavior already implemented. Do not rebuild on resize/fold-only renders.
-   Unify navigation generation checks across choose, applyPath, refresh and root/source changes. Capture the intended adapter for in-flight work. Abort fetches when practical and make each preview own/revoke its object URLs even when its result becomes stale.
-   Acceptance: resize/folding causes zero new preview-provider calls; scrolling/media position stays stable; saved/changed bytes invalidate correctly; delayed old navigation or preview completion cannot replace the current selection or mutate another editor; fullscreen and return focus remain consistent.
-   Verification: spy provider call counts, delayed-read ordering, rapid Back/Forward, switch server/local mid-read, save then refresh, and \[39\]/\[40\]/\[64\] desktop/portrait fixtures. Keep existing relative performance budgets rather than inventing unsupported global timing targets.
-   Documentation: restore \[21\]'s acceptance criteria in current source and record dated regression evidence; update preview lifecycle/port comments. No persistent migration. Roll back cache optimization independently if invalidation fails, retaining navigation stale-work guards.

### 10\. Bound work at acquisition points

Addresses F12; follows the source/preview/listing contracts established above.

-   Stream ripgrep output with a global byte/match budget and terminate/reap the process when the budget or deadline is reached. Handle cancellation where the request lifecycle permits it. Return explicit partial/truncated results rather than labelling partial output as a complete search. Handle non-UTF-8 path/line events.
-   Bound body/file reads before allocating complete payloads; offload blocking filesystem work from async save handling. Bound office/archive expansion and conversion where feasible. Avoid re-enumerating a whole directory on every page if measurement shows material cost.
-   Measure representative current-scale cases before adding worker pools/caches. Keep the existing simple FSA metadata strategy unless its measured concurrency causes responsiveness problems; then add a small explicit concurrency bound.
-   Acceptance: query/result/body/archive limits cap actual work, not only the final JSON; child processes are reaped on cancellation/timeout; the app remains responsive; no truncated text is silently editable as if complete.
-   Verification: instrument bytes read, rows/queries examined, subprocess lifetime and retained output with generated temporary fixtures. Benchmark directory and metadata operations relative to the same-run baseline. Update \[49\]/\[60\] and operational documentation with measured bounds. No disk migration; API clients must understand partial-result status. Rollback can lower limits, not remove them.

### 11\. Publish one accurate current architecture and close the evidence loop

Addresses F13 and the remaining baseline from F4. Documentation updates belong in each earlier step; this final pass checks consistency.

-   Update root/server README, contribution guides, static guide, SECURITY.md, CHANGELOG and adapter/port docs with verified commands, source/renderer matrix, write/delete authority, cache policy, actual PPTX behavior, CLI environment precedence and external deployment assumptions.
-   Preserve the dated previous review and task history. Mark superseded ADR decisions with links and dates. Turn ROADMAP into a current status/dependency index instead of instructions to repeat completed deletions. Remove dead API/provider code only after confirming no supported route/import uses it; specifically, deleting JSON provider registration still needs a replacement for server deep-link validation of browser-owned JSON paths.
-   Send the earlier tracker-maintenance work a review handoff through the plan, listing overlaps and contradictory states. Do not change statuses, delete task documents, renumber tasks, or infer completion solely from this review. No external message is needed or authorized here.
-   Acceptance: every advertised test command executes checks in a clean environment; package/wheel imports and asset graph work outside the source tree; bundle/dev/server regression suites and chosen lint/type gates pass; stale claims are dated history rather than current instructions. The changelog identifies user-visible regressions fixed, not just refactoring.
-   Verification: documentation command smoke tests, local-link check, installed-wheel server asset/preview smoke, full headless CI, manual FSA checklist and one installed-PWA upgrade/recovery check. Reconcile each finding with its acceptance evidence before closure.
-   No user-data migration. Documentation changes are independently reversible. Keep native \[29\] → \[30\] → \[31\] deferred until browser correctness and \[21\]'s prerequisite are real; no framework, bundler replacement, general ViewSpec, native toolkit or service orchestration is justified by this review alone.

The order first restores a minimal trustworthy check path, closes demonstrated authority leaks, and protects writes. It then fixes stale delivery, broken operations and addressability before optimizing expensive work. That yields direct user value while retaining the existing shared UI and its measured small-project tradeoffs.

## Lower-priority findings and follow-up checks

-   Confirmed descending name-sort defect: `state.js:visibleKids` returns adapter order whenever key is name, ignoring desc. The probe returned `[a,z]` for descending. Fix with step 6 and test both adapters; preserve deliberate virtual ordering separately.
-   Confirmed invalid page input becomes HTTP 500: `app.py:rt` calls int without validation. Return a bounded 400 response for malformed pagination input; do not replace the small router shim with a framework solely for this.
-   Virtualization in `render.js:paintRange/makeRow` only adds rows and never evicts them. It limits initial DOM construction, not retained DOM after a complete scroll. `ROW_STEP` is fixed while density changes row styling. Verify long scrolling at both densities before claiming 100,000-row support; no new virtualization library is warranted without a failing measured case.
-   IndexedDB `kvPut` is not awaited to transaction completion, database connections are not closed, and rememberRoot performs a read/modify/write across async operations. Multi-tab lost updates and failed persistence are risks, not reproduced data loss. Add deterministic transaction/concurrent-save checks before redesigning storage.
-   Core rows are clickable divs with labels but no complete tree/list selection semantics; refresh controls have negative tabindex. Audit screen-reader selection announcements and keyboard access to row actions against the cross-device goal. This review did not perform an assistive-technology audit.
-   The concatenating builder deliberately imposes a shared lexical namespace across modules. Its collision regex is limited, but the source graph is small and explicit; retain it with parse/build parity checks unless a concrete unsupported module feature forces change. Do not add a frontend toolchain for hypothetical growth.
-   Duplicate Python/browser VTT and classification logic, unused provider-rendering paths, debug globals, DOM singleton coupling and HTTP-aware core search deserve targeted cleanup after behavioral tests. Reuse \[29\] only for genuinely pure functions needed by tests; extraction is not the first remediation.
-   Native OS picker permissions, network-share stalls, browser-specific local-network policies, raw website compatibility, host proxy access control, CDN availability and actual service definitions remain operational verification items. No claim is made that the public demo is safely configured or currently running this exact commit.

## Completion boundary

The review and ordered plan are complete for user review. Findings distinguish direct reproductions, source-confirmed defects, and risks needing further verification. Existing task/ADR history and user edits are preserved. No proposed fix has been implemented, no deployment or additional task was created, and no repository change remains.
