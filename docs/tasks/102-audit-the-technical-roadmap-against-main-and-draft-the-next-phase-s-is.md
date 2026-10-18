---
depends-on: [101]
---

# Audit the technical roadmap against main and draft the next phase's issues

Steward issue, 2026-10-18. Goal: agentic-leverage (filemill is a tier-1
project in `<steward-vault>/Goals.md`). filemill's Ordered
backlog and Unverified proposals are empty, while `docs/ROADMAP.md` lays out
nine phases, each "small enough for one task", with "Done when" checks.
Nothing records which phases are done since [25], [87], [93], [99] and
others landed. This issue gives the steward the next filemill backlog to
file.

It depends on [101], the browser-test issue, only so that two filemill worktrees
are not created at once: a Claude worker's sandbox holds a lock in the
shared `.git/`, and T3 then cannot create a second worktree.

## Work

1. For each phase and each numbered step, decide done, partly done or open
   on today's `main`, and cite the commit, issue, ADR or file that shows it.
   Run the cheap "Done when" checks (greps, line counts,
   `pre-commit run --all-files`). For test-suite checks, cite the recorded
   runs in [99], [100] and [101] instead of rerunning the
   full suites.
2. Note the steps the code has overtaken (for example ADR 0067 for Phase 0
   step 2) and any that no longer fit `docs/GOALS.md`.
3. For the first phase that is not done and the one after it, draft issue
   texts in this file: title, goal, work, ground rules and acceptance, each
   sized for one agent run of about an hour, split where a phase is larger.
   Name the questions Antti must answer before a draft can start.
4. Propose status annotations for `docs/ROADMAP.md` as a patch in this
   file. Don't apply it.

## Ground rules

- Change only this description file and the issue's tracker moves.
- Don't push, deploy or restart services.

## Acceptance

- A table of every phase and step with status and evidence.
- Draft issues for the next two open phases, with their open questions.

## Audit, 2026-10-18

Baseline: local `main` at `26a77d60ff8e5d3c9f2fbacfbc289e1fafe9c482`, also
this worktree's starting HEAD. No fetch, product change or full-suite rerun
was needed. Issue [101] is completed, awaiting acceptance. Read
`docs/ARCHITECTURE-REVIEW.md` first; its A1–A12 findings and remediation
order take precedence over the old roadmap. This audit does not assert that
passing tests resolve those findings.

The roadmap has **ten phases, 0–9**, not nine. It also skips Phase 2 step 4.
The tables preserve its numbering. Status means:

- **Done:** the intended result exists, sometimes through a later design.
- **Partly done:** some work exists, but a stated outcome or check is missing.
- **Open:** the requested result is absent.

A done implementation does not imply user acceptance. No other issue's state
is changed. Evidence paths below are relative to the repository root.

### Phase and step inventory

| Phase | Status | Evidence and remaining work |
| --- | --- | --- |
| 0, green and honest | Partly done | Local suites and bundle are green in [99]/[101]; stale current documentation and unverified current-main CI remain. |
| 1, gates | Partly done | All six local hooks pass. Unlinked suppressions violate its final check; remote CI evidence does not cover local main. |
| 2, one document per fact | Partly done | Tracker consolidation, ADRs and root documents exist; duplicate/stale prose and over-40-line ADRs remain. |
| 3, module graph | Partly done | ES modules and an acyclic graph exist; all of core is not DOM-free, core still tests `vpath`, and the port field list is incomplete. |
| 4, state/render discipline | Partly done | Name-based selection, split layout arithmetic and responsive checks exist. Preview reuse and some named constants do not. |
| 5, kind and order | Done | [6]/[7], classification tables, producer ordering and descending-order regression are implemented. |
| 6, minimal server | Partly done | Browser Markdown/DOCX, Starlette, paths/PWA modules and byte/shell routing exist. Python previews, `/w/` and 2,491 Python lines remain. |
| 7, one harness | Partly done | [25]/[99], condition waits and root pytest exist. Separate browser lifecycles and no established `-n auto` pass remain. |
| 8, preview/editing | Done | Registry, CSV/video/browser PPTX, RST experiment and editor modules exist. The proposed unconditional preview-API deletion is superseded. |
| 9, native shells | Done | DOM-free model, native three-port host, UI qualification [30]/ADR 0079 and toolkit decision [31]/ADR 0066 exist. Prototype limits remain explicit. |

| Phase.step | Status | Evidence and disposition |
| --- | --- | --- |
| 0.0 | Done | `static/build-index.py --check` passes, 351,147-byte bundle; bundle hook exists. |
| 0.1 | Done | `a6535049`, `0fd40da9`, `686cd25d` delete finder routes, `columns.py`, SQLite fragments and COLUMN_JS/CSS. `rg -n 'htmx|COLUMN_JS' server/src` has no matches. |
| 0.2 | Done | [33] returns the shell; ADR 0067 and `urls.py` remove `no-columns` altogether. Do not restore that layout. |
| 0.3 | Done | `94019d6a`, `docs/adr/0001-one-finder.md` choose the shared finder. Its `/api/render` text now needs a dated historical correction under 0.5/2.7. |
| 0.4 | Done | `ui/core/model/state.js` honours `ordered`; JSON/JSONL/CSV adapters set it. [25]/[99] replaced abort-prone scripts with separate pytest tests. [101] records all suites passing, including editor checks. |
| 0.5 | Partly done | `server/TASKS.md` is consolidated/deleted and completed task records retain history. `server/README.md` still lists `rendering.py`/live mode; `server/CONTRIBUTING.md` still prescribes `/api/render`, `preview-upload.js` and 100% branch coverage. A11 remains open. |
| 0.6 | Done | `4025d15c`, root `LICENSE` contains MIT terms. |
| 0.7 | Done | `ad83e995` removes hotreload, forgetRoots and unused formatter/style code. `styles.py` is now absent too. `preview.py` still uses a Pygments formatter at runtime; that is not the unused formatter targeted here. |
| 1.1 | Done | `server/pyproject.toml` declares dev ruff/mypy and 88-column formatting; uv.lock fixes resolved versions. Ruff infers Python 3.12 from `requires-python >=3.12`, so a separate target-version is unnecessary. Hooks pass. |
| 1.2 | Done | `providers/sqlite.py` has no S608 suppression; identifiers are double-quoted with embedded quotes escaped. The surviving S110 comment is a separate exception-policy debt. |
| 1.3 | Done | `d63043c6`, `61656c23`, `deno.json`; CI pins Deno 2.6.8 and checks first-party UI. Vendored sources are excluded deliberately. |
| 1.4 | Done | `.pre-commit-config.yaml` has ruff, ruff-format, mypy, deno fmt/lint and bundle checks; all pass here. |
| 1.5 | Done | `.github/workflows/publish.yml` has `test.needs: lint`, and publishing needs both. [90]/[94] strengthen the matrix/actions. Installing hooks and branch protection are not established by this file. |
| 1.6 | Done | Root `pytest.ini` has no coverage addopts; CI's server leg supplies `--cov` and `--cov-branch`. |
| 2.1 | Done | Root `TASKS.md` and `docs/tasks/` replace all three edition-local tracker/issue files, which are absent. See [95]'s historical reconciliation. |
| 2.2 | Done | All three PLAN files and `server/lmt/` are absent; current port/edition contracts live in root docs and ADRs. |
| 2.3 | Partly done | Root README explains editions/ports; `server/README.md` and `static/AGENTS.md` still repeat architecture and stale preview/network facts. |
| 2.5 | Partly done | [15], `docs/adr/`, and ADR links in `static/AGENTS.md` exist. Fourteen ADRs are at least 40 lines; the largest is ADR 0064 at 162. The literal size rule fails. |
| 2.6 | Done | Root `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md` exist. Their existence does not settle A3/A5's security-document accuracy findings. |
| 2.7 | Partly done | STE guidance and portability/Playwright guards exist, but current README's CDN PPTX viewer claim contradicts `preview-rich.js`; A11 lists further contradictions. Not every claim is mechanically verified. |
| 3.1 | Done | All first-party core/adapter JS files are ES modules; `ui/entry-static.js`, `entry-server.js` and later `entry-native.js` exist. |
| 3.2 | Done | `static/build-index.py` traverses/concatenates the graph and retains a passing `--check`. |
| 3.3 | Done | `static/index-dev.html` loads entry-static; `app.py`'s shell loads entry-server with an import map. No hand-maintained core script sequence remains. |
| 3.4 | Done | Import-graph scan found no cycles. `render.js:setActions` receives callbacks at boot; `layout.js` imports write guards from `dom.js`. |
| 3.5 | Done | JSON virtual code is in `adapters/vfs-json.js`; edition welcome/Open Folder markup is in app adapters, local badge/leave controls in app-http, rich toggle in preview-rich. `shell.js` retains shared chrome. |
| 3.6 | Partly done | `ports.js` documents FS/PREVIEW/ROUTER and RouterPath.base, but HTTP nodes also carry `abs` and `fileKind`, absent from its field list. Update the contract before declaring every field covered. |
| 3.7 | Done | `core/limits.js`, `core/mount.js:mountRoot`, `core/model/deeplink.js:currentPath`; no `pathParts` remains. Model extraction moved the original paths. |
| 3.8 | Done | `adapters/vfs-json.js:withVirtual` handles both JSON and JSONL; old withJson/withJsonl wrappers are absent. It does not need a speculative generic spec argument. |
| 4.1 | Open | [21], A9, `render.js:renderPreview` creates an element and calls `PREVIEW.revoke` on every non-editor render. [97] prevents delete/read races but does not cache previews. ADR 0079 measures the native cost. |
| 4.2 | Done | `model/selection.js`, `model/state.js:rowIndex` use selected names; no `cursor[i]` or `lastSel` code remains. ADR 0005's old contract needs a supersession note. |
| 4.3 | Done | `layout.js` has foldFromScroll, applyWidths, panFocus, slideTail, each below 25 lines. `applyScroll` remains a small coordinator; the literal demand that its name disappear is obsolete. |
| 4.4 | Partly done | Named timing/layout values exist, but [95] L041 records remaining fold epsilons/virtual overscan; `layout.js:wideCount` still uses an unnamed `1e-9` epsilon. Scope constants to measured behavior, not every arithmetic zero/one. |
| 4.5 | Done | ADR 0062 plus 0075/0076 describe the layout. `test_browser_new_ui.py::test_responsive_widths_survive_keyboard_and_mouse` covers desktop, 1024×768 tablet, portrait and landscape; keyboard suite adds geometry/touch coverage. |
| 5, classification [6] | Done | `883fdee6`, `7fbbcef5`, `core/file-kind.js`, `vfs.py:classify_path`, `server/tests/test_file_kind.py:CASES` and `static/tests/test_ui.py::test_file_kinds` give shared-by-value cases. |
| 5, ordering [7] | Done | `db21b97e`, `b3fc7f53`; `api.py` orders HTTP listings, `fsa.js` orders local entries, model visibleKids preserves `ordered` and reverses within groups for descending. Tests in `test_api.py` and model/test.mjs cover the contract. |
| 6.1 | Partly done | Markdown/DOCX use pinned `ui/vendor/` modules in both editions; `rendering.py` and Python Markdown/Mammoth dependencies are gone. Runtime Pygments remains in `preview.py` and dependencies. |
| 6.2 | Partly done | [33], `urls.py`, `app.py:resource`, ADR 0067 and [89]/ADR 0077 implement byte/shell routing and shared view switching. Legacy representation helpers are absent, but `preview.py:render_source` remains. |
| 6.3 | Done | [34], `providers/sqlite.py` returns data, no HTML render_preview; browser JSON/record rendering displays it. [9] is closed. |
| 6.4 | Partly done | `/api/render`, preview-upload.js, SSE/live reload, styles.py and `/raw?path=` route are gone. `/w/` remains without the old CORS headers. A decision with its consumer is still needed, not blind deletion. |
| 6.5 | Partly done | `paths.py`, `pwa.py`, `_zones(request)` and loopback default exist. `app.py` is 510 lines and still handles previews/resource HTML and API orchestration, beyond routing only. |
| 6.6 | Done | `server/pyproject.toml` declares Starlette/Uvicorn, no python-fasthtml. Shell is a string template in app.py. |
| 6.7 | Done | `docs/tasks/9-vfs-viewspec.md` explicitly closes the old interface proposal via [34]. A fourth provider alone is not grounds to add ViewSpec without the measured interface problem required by the architecture review. |
| 7.1 | Done | [25]/[99], merged `adb7aef3`, root uv workspace/lock and pytest.ini discover server and static suites; static sections use fixtures under static/tests. |
| 7.2 | Done | `ffc5dbf4` removes fixed waits, [101] adds folder-readiness waits. Recursive guard `server/tests/test_browser_waits.py`; no literal wait_for_timeout under static or server/tests. |
| 7.3 | Partly done | Root sync/async Playwright fixtures exist and keyboard proxy plumbing is gone. Keyboard `_ui_page` still starts sync_playwright separately; static fixtures own async contexts. [95] L044 records the incomplete consolidation. |
| 7.4 | Done | `6e7ee5be`, `static/FSA-TEST-CHECKLIST.md` document manual test-e2e.py, which has a main guard. |
| 7.5 | Partly done | Root conftest monkeypatches `app.state.root`, not a module global ROOT. No xdist dependency or recorded root `pytest -n auto` pass; parallel CI suites are not parallel tests within one suite. [95] L048. |
| 8.1 | Done | [26], `core/renderers.js:CORE_RENDERERS`, RICH_RENDERERS and both app adapters register `{kind, render, fallback}` entries. |
| 8.2 | Done | CSV adapter and video registry entry exist; `preview-rich.js:pptxHTML` reads slides in-browser. python-pptx is dev-only for test fixtures. `/api/preview` remains for RST/VTT/archive members; [95] L099 records why deletion cannot follow PPTX alone. |
| 8.3 | Done | [27]/ADR 0064 measure pinned Pyodide/docutils transfer and first-load times, concurrent rendering, consent and fallback. This was an experiment, not proof of full edition parity today. |
| 8.4 | Done | `ui/editor/{undo,find,gutter,modified,editor}.js` implement the requested additions through FS.write. Static editor tests are included in [99]/[101]. Save atomicity/conflicts remain separate A4 work. |
| 9.1 | Done | [29], `core/model/{state,selection,folding,keyboard,deeplink}.js` and test.mjs are DOM-free; `dom-renderer.js` holds DOM handles. This satisfies the model-package intent, not a claim that all core files are DOM-free. |
| 9.2 | Done | [30]/ADR 0079 qualify direct WebKitGTK over Tauri: 444,520-byte stripped executable, native three ports, 220 UI scenario checks passing in 4/5 runs. One timeout in five and missing native deletion/remembered roots remain recorded limitations. |
| 9.3 | Done | [31]/ADR 0066 compares AppKit/GTK4/WinUI and retains WebView. Its 2026-10-17 update refers to qualification ADR 0079. Full native product parity remains future work. |

### Cheap checks and recorded validation

No full suite was rerun for this documentation audit. These are the recorded
runs, in order, so the failed middle checkpoint is not hidden:

| Source | Baseline | Recorded result |
| --- | --- | --- |
| [99], completion 2026-10-17 | merged `adb7aef3` main tree | Root pytest 1,000 passed in 815.02 s; server 853 passed twice, 806.51/548.89 s; bundle 147 twice, 463.40/490.01 s; dev 147 twice, 494.70/506.02 s. Six pre-commit hooks passed. |
| [100], evidence 2026-10-17 | `defedeb2` | Server 851 passed/2 failed in 701.49 s, a sandbox document-path failure and missing folder-readiness wait. Bundle/dev each 147 passed, 473.61/493.90 s. These failures were not attributed to the reviewed product items. |
| [101], rebased validation 2026-10-18 | implementation `cd42c383`, after portability correction `3425fbe5`; merged into main before this audit | Server 853 passed twice, 759.82/533.63 s; bundle/dev each 147 passed, 582.34/604.00 s. Resolves the failures above. |

Checks run here against the unchanged product tree:

| Command/check | Result and interpretation |
| --- | --- |
| `uvx pre-commit run --all-files` | All six hooks pass. No formatter changes. Equivalent invocation of the requested pre-commit command through uvx. |
| `static/build-index.py --check` | Pass, 351,147 bytes. No rebuild needed. |
| `rg -n 'htmx|COLUMN_JS' server/src` | Exit 1, no matches. Phase 0 deletion check passes. |
| `rg -n 'wait_for_timeout' static server/tests` | Exit 1, no matches. Phase 7 wait check passes. |
| `rg -n 'raw\?path|sse/reload' server/src` | Exit 1, no matches. Phase 6 obsolete-route check passes. A test still asserts the old raw route returns 404. |
| `rg -n '# noqa' server -g '*.py'` | Six occurrences, none with an issue link: cli.py B008, vfs.py F401, preview.py S110 twice, sqlite.py S110, test_browser_waits.py FLY002. Phase 1's final exception check fails. |
| `git ls-files '*.md' \| xargs wc -l` | 11,414 lines before this audit. The actual command follows tracked Markdown symlinks. |
| `git ls-files '*.py' '*.js' '*.css' \| xargs wc -l` | 28,772 lines, including tests/vendor sources. Prose/code inequality passes; it is not proof that prose is correct or minimal. Git blob newline counts on main are 11,159 Markdown versus 28,772 code, avoiding symlink dereferencing. |
| Count `server/src/filemill/**/*.py`, including direct children | 2,491 lines. The literal Phase 6 target below 1,500 fails. New archive/Git-bundle providers alone contribute 462. |
| AST scan of production Python imports | Function-local zstandard imports at archive.py:60 and :68 remain, for Python-version compatibility. Phase 6's zero-local-import check fails; avoid deleting supported decompression to satisfy it. |
| Scan ADR lengths | Fourteen files have at least 40 lines, so Phase 2's under-40 rule fails. Measured ADR 0064 has 162. |
| Recursive relative ES-import scan of first-party UI, excluding vendor | No cycles. The bundle check independently validates the built graph. |
| Phase 3 grep, corrected to recursive `rg -n 'vpath\|showDirectoryPicker\|PreviewLocal\|\bAPI\b' ui/core` | Executable vpath tests remain in render.js/file-kind.js; API also occurs in comments. No showDirectoryPicker or PreviewLocal. The intended adapter-independence check is incomplete. |
| `deno eval 'import {sortKids} from "./ui/core/sort.js"; console.log(sortKids)'` | Fails: sortKids is no longer exported there. Overtaken check, not a sorting regression. Import/call from `ui/core/model/sort.js` passes with no DOM. |
| Read render/layout code | Preview element recreation remains; zero-fetch-per-resize is not met. Four split layout helpers are below 25 lines; applyScroll remains their coordinator. |

Remote CI is a separate check. Read-only `gh run list --branch main
--workflow publish.yml --limit 1 --json status,conclusion,headSha,url` reports
[run 38957407184](https://github.com/akaihola/filemill/actions/runs/38957407184),
completed with failure for `ff7b3143`, not this audit's local `26a77d60`.
That run's lint, bundle and dev jobs passed; its server job failed and publishing was skipped. This does not establish CI for today's local main. [93]/[94] already retain
that delivery check; no replacement CI issue is needed. No push or workflow
dispatch was made.

The remaining "Done when" claims need these qualifications. Phase 0's
latest local suite proof is [101], while current-main remote CI is unproved.
Phase 1's latest observed remote lint job passed only on the older remote
SHA. Phase 2's prose ratio passes, but its "every claim" test fails on the
named stale claims. Phase 4's existing render-budget tests are included in
[101]'s green suites, while its zero-preview-fetch assertion is still unmet.
Phase 5's acceptance is covered by the named classification/order tests.
Phase 6 shares Markdown modules/rules across editions, but no new exact-HTML
comparison was run here; its numeric/import/dependency targets still fail.
Phase 7's root-command proof is [99]; a within-suite parallel run is unproved.
Phase 8 has the requested table and registry tests; classifying an entirely
new file kind can also require the central classifier, so "one entry" is a
renderer-extension rule, not a literal total-file-change budget. Phase 9's
native-scenario proof is [30]/ADR 0079, with its 4/5 reliability limit.

### Overtaken requirements and goal conflicts

- Phase 0.2 is closed by ADR 0067. Reintroducing no-columns would restore a
  removed layout contract.
- Phases 0.4 and 7.1 must name pytest sections, not deleted static/test-*.py
  entry points. Root pytest is delivered, while both static modes still need
  their separate runs. Native qualification covers the UI scenario, not every
  automated browser test through native FS.
- Phase 3's DOM-free promise belongs to `core/model/` after [29]. A
  DOM-based shared renderer is intentional for browser editions and WebView.
  Core's direct vpath tests and HTTP search URL remain adapter-boundary debt,
  not a reason to import a framework or rebuild the renderer.
- Phase 4's split is delivered without removing the applyScroll coordinator.
  Requiring a function rename/deletion adds no product value. Preview cache
  acceptance still applies and directly serves GOALS' resize budget.
- Phase 5's "still open" wording is obsolete. Preserve adapter-owned order,
  including the descending fix, rather than restoring duplicate sorting.
- Phase 6's four-dependency/1,500-line targets predate required RST, archives
  and Git bundles. GOALS explicitly wants office/database previews and few
  justified dependencies. Remove redundant rendering only after equivalent
  browser behavior exists. Docutils/zstandard now have concrete consumers;
  python-pptx is fixture-only. Keep limits and root safety when reducing code.
- Phase 8.2's unconditional `/api/preview` deletion no longer follows from
  browser PPTX. RST, WebVTT and archive member previews still use it. Full
  office fidelity also exceeds the delivered PPTX text extraction.
- Phase 9's prototype is delivered, not a released macOS/GNOME/Windows
  application. GOALS' "This is not built yet" needs to distinguish the Linux
  prototype from the future product. ADR 0079 records flaky native resize.
- Fixed ADR line caps and "one task per phase" are poor proxies for the
  measured evidence and hour-sized work requested here. Keep evidence, split
  work, and have Antti decide whether the literal caps remain policy.
- A11's documentation corrections must not claim A1–A5 are fixed. The
  architecture remediation order takes priority over new feature work. Those
  security/correctness findings need their own measured, regression-tested
  implementation issues, outside these two early-phase documentation/gate
  drafts. This audit does not change ARCHITECTURE-REVIEW.md because [102]
  explicitly permits only its description and tracker moves.

### Next issue drafts

The first unfinished phase is **0**, followed by **1**. Drafts below close
those phases' remaining work. They are text for the steward to file, not new
tracker entries or allocated numbers. Each is bounded to about one agent hour.
Use draft labels as dependencies until the steward assigns real issue IDs.
Later partial phases do not block these corrections. A1–A5 implementation
must retain priority when the steward orders the wider backlog.

All drafts inherit these ground rules: read the architecture review first;
change only the named scope; preserve recorded measurements and user
acceptance; use red-green tests for any new guard or bug fix; no push,
deployment, restart, remote settings change or unrelated refactoring. End by
recording exact validation and remaining limits. Existing tests need not be
rerun as full suites for prose-only changes.

#### Draft 0A: Correct the current edition and renderer documentation

Goal: a contributor learns today's preview, network and startup behavior from
the current documents. Covers Phase 0.5 and the overlapping A11 facts.

Work, 45–60 minutes:

1. Check README.md, server/README.md and server/CONTRIBUTING.md against
   cli.py, app.py, preview.py, preview-rich.js and the CI workflow.
2. Replace the advertised CDN PPTX viewer with the actual text extraction;
   distinguish static consent-gated RST from server Python RST and vendored
   Markdown/DOCX. Correct the removed rendering.py, upload renderer, live flag
   and false 100% coverage instructions. Link repeated edition architecture to
   the root README rather than copying it.
3. Correct static/AGENTS.md's no-network/read-only claims against FS.write,
   remove, and rich-preview consent. Retain its scoped testing instructions.
4. Date the corresponding A11 corrections. Do not declare the remaining
   security findings resolved.

Ground rules: current operator/contributor facts only. Do not change code,
GOALS' product policy, SECURITY.md's write authority policy, or old task
measurements. Leave a named residual if correcting it would require choosing a
new behavior. Keep all development examples portable.

Acceptance:

- Every corrected command/renderer claim cites its current implementation.
- No current run instructions mention a removed module, route or CLI flag.
- `uv run pytest server/tests/test_docs.py -q` and all six pre-commit hooks
  pass. Record code-based verification for CLI examples that start services;
  this documentation task does not restart a running instance.
- Root README gives an accurate edition/renderer table; other documents link
  to it for shared facts. No unverified full office-rendering claim remains.

Questions for Antti before starting: none for factual corrections. If the
existing text expresses a desired future PPTX viewer, keep that intent in a
clearly marked proposal rather than choosing a replacement viewer here.
Dependencies: [102].

#### Draft 0B: Date superseded roadmap and historical document claims

Goal: readers can distinguish old requirements, delivered work and current
instructions without erasing history. Completes the remaining Phase 0 honesty
work and prepares Phase 2's consolidation.

Work, 45–60 minutes:

1. Review and apply or adjust the proposed roadmap status patch below.
2. Add dated supersession notes to ADR 0001's upload-render route, ADR 0005's
   lastSel contract and ADR 0034's read-only mode. Cite the replacing code,
   task or ADR. Preserve their original decision/measurement text.
3. Read docs/tasks/2-fix-all-test-failures.md and the completed editor-cursor
   item. Mark any current-looking old commands/assertions as historical;
   retain failures, original acceptance and their later outcomes.
4. Date the relevant A11 resolution notes, naming current open work. Do not
   turn [93]/[94] into completed delivery checks.

Ground rules: docs/ROADMAP.md, the three named ADRs, the named historical
record, factual ARCHITECTURE-REVIEW/GOALS updates only. If GOALS changes, clarify
that a Linux prototype exists but cross-platform native applications remain
future work. Do not revise product goals or rewrite closed-task acceptance.
Do not move any other issue or change its acceptance checkbox.

Acceptance:

- Roadmap status matches this audit's baseline or cites later main changes.
- No superseded ADR reads as an instruction to restore removed behavior.
- Historical editor/test records retain the original evidence, with later
  corrections dated separately.
- Documentation checks and pre-commit pass; no implementation files change.

Questions for Antti before starting: approve the proposed roadmap status and
confirm that its under-40-line ADR rule, 1,500-line/four-dependency server
budgets and one-task-per-phase claim may be replaced by evidence-based
criteria. If those policies remain, annotate their failed checks explicitly;
do not silently waive them. This approval is required for changing policy,
not for dating factual supersession notes.
Dependencies: [102], Draft 0A for consistent current facts.

#### Draft 0C: Record CI delivery proof for the audited main

Goal: Phase 0 and Phase 1 completion refer to a successful workflow on the
actual delivered main, not a local pass or an old failed SHA.

This is a **validation slice of existing [93]/[94]**, not another issue to
file. Keep their identities and acceptance pending. Expected agent time is
15–30 minutes once an authorized main update is available.

Work:

1. Read the delivered main SHA and its existing publish workflow run.
2. Record the lint, server, bundle and dev conclusions and run URL in the
   existing issues. If no run covers that SHA, leave the delivery check open.
3. If a job fails, identify the first failed check and separate a new regression
   from the already recorded failure. File a focused reproduction separately
   rather than fitting code changes into this validation slice.

Ground rules: read-only workflow inspection and [93]/[94]'s evidence/state
updates only, under a separately authorized continuation of those issues.
This draft does not authorize a push, dispatch or deployment. A passing local
suite is not CI evidence. Do not rerun suites merely to fill the document.

Acceptance: one run URL and exact main SHA cover successful lint and all three
suite jobs, or a precise blocker keeps the issues open. Completion uses `[ ]`,
never user acceptance `[x]`.

Questions for Antti before starting: which delivered SHA should [93]/[94]
validate, and will Antti handle any required history publication? The latest
remote run observed here is for `ff7b3143`; it cannot validate `26a77d60`.
Dependencies: existing [93]/[94] publication prerequisites, not duplicate new
tracker dependencies. Drafts 0A/0B can proceed before this external check.

#### Draft 1A: Reconcile lint and skip exceptions with the documented gate

Goal: the Phase 1 "no unlinked noqa" check is true and stays true, while the
existing meaningful checks remain enabled. Also account for the roadmap's
unlinked skipped-test rule without expanding lint rule families.

Work, 45–60 minutes:

1. Inventory the six noqa occurrences listed above. Ask the configured ruff
   which suppressions are needed; remove obsolete ones. For an unavoidable
   suppression, cite a focused existing issue or have the steward file its
   concrete exception rationale. Do not use one blanket audit link.
2. Review the unconditional PPTX skip in test_preview.py. It says extraction
   was replaced by LibreOffice, while main now extracts text in the browser.
   Remove the obsolete test if it tests retired Python behavior; otherwise
   name the missing contract and link its focused issue. Keep environment
   dependency/platform skips conditional and justified.
3. Add one small regression guard for first-party Python suppression links,
   with failing fixtures for a bare suppression and passing fixtures for the
   chosen issue-link syntax. Run it in the existing gate. Match the scope and
   syntax already used by the repository; do not build a general policy engine.
4. Record inferred Python target selection, Deno pin, local hook installation
   instructions and CI dependencies. Distinguish the installed hook command
   from proof that every contributor or protected branch enforces it.

Ground rules: suppression sites, obsolete skip, focused guard, existing gate
configuration and contributor instructions only. Keep security behavior,
provider registration and Python-version compatibility. Do not enable a broad
new ruff ruleset or change branch protection. Split any behavioral fix found
here into its own reproduction and issue.

Acceptance:

- Every remaining first-party noqa carries the agreed issue reference.
- The guard demonstrably fails before the correction and passes afterward.
- The obsolete unconditional PPTX skip is removed or has a current, linked
  unmet contract. Conditional environment skips retain clear reasons.
- Focused tests and `uvx pre-commit run --all-files` pass. Draft 0C separately
  supplies exact-main CI proof; no remote delivery is claimed by this patch.

Questions for Antti before starting: retain the literal issue-link policy or
allow a documented permanent-exception class for import registration and
best-effort fallback? The draft assumes the literal policy unless Antti
changes it. Should local pre-commit plus CI remain the enforcement boundary,
or is repository branch protection wanted? A settings change needs separate
authorization and is not part of this draft. Neither question blocks removing
provably unused suppressions or the stale skipped test.
Dependencies: [102]. Can run alongside the Phase 0 documentation drafts;
retain CI validation under [93]/[94].

### Proposed roadmap status patch, not applied

This patch adds status and failed-check notes without rewriting the original
steps. Applying it is Draft 0B work. Keeping the original text makes the
historical prescriptions visible until Antti decides the policy questions.

```diff
--- a/docs/ROADMAP.md
+++ b/docs/ROADMAP.md
@@ -3,5 +3,13 @@
 This roadmap closes the gap between `docs/ARCHITECTURE-REVIEW.md` and
 `docs/GOALS.md`. Phases are in dependency order. Do them in order. Each phase
-is small enough for one task in `TASKS.md`.
+was originally intended to fit one task in `TASKS.md`.
+
+Audit, 2026-10-18, main `26a77d60`: there are ten phases, 0–9.
+The phase and step evidence is in issue [102],
+`docs/tasks/102-audit-the-technical-roadmap-against-main-and-draft-the-next-phase-s-is.md`.
+Phases have since overlapped; split remaining work into bounded issues.
+`docs/ARCHITECTURE-REVIEW.md` takes precedence where this sequence conflicts
+with its remediation order. Local validation does not establish remote CI
+or user acceptance.

 Each phase has the same shape:
@@ -17,4 +25,8 @@

 ## Phase 0: green and honest
+
+Status 2026-10-18: partly done. Steps 0–4, 6 and 7 are implemented;
+step 5's current-document corrections remain. [99]/[101] record green local
+suites. [93]/[94] still need CI proof for delivered main. ADR 0067 retires step 2.

 **Goal.** Both test suites are green on `main`. Every document describes the
@@ -69,4 +81,9 @@
 ## Phase 1: gates

+Status 2026-10-18: partly done. Steps 1–6 and all six local hooks pass.
+Six unlinked noqa suppressions still fail the final exception-policy check.
+Deno is pinned in CI; Ruff infers its Python target from requires-python.
+The latest observed remote lint pass is on an older SHA, not audited main.
+
 **Goal.** A formatting or lint error cannot be committed or merged.

@@ -99,4 +116,9 @@

 ## Phase 2: one source of truth for documents
+
+Status 2026-10-18: partly done. Steps 1, 2 and 6 are implemented;
+3, 5 and 7 retain duplication/stale claims or fail the ADR size rule.
+Prose is below code by line count. Step 4 is absent from the original numbering.
+Historical measurements must remain distinct from current instructions.

 **Goal.** Each fact lives in one document. Every document is in Simplified
@@ -134,4 +156,9 @@

 ## Phase 3: make the shared UI a module graph
+
+Status 2026-10-18: partly done. Steps 1–5, 7 and 8 are implemented;
+step 6 misses some node fields. The DOM-free package is now core/model/,
+where sortKids can be imported. Core vpath checks and HTTP search coupling
+remain; the bundle and acyclic-module checks pass.

 **Goal.** `ui/core/` can be imported without an HTML file, without a DOM
@@ -177,4 +204,9 @@
 ## Phase 4: state and render discipline

+Status 2026-10-18: partly done. Steps 2, 3 and 5 are implemented;
+step 1's preview reuse is open and step 4's constants cleanup is partial.
+applyScroll remains as the coordinator of the four extracted helpers.
+A9 and ADR 0079 record the remaining preview recreation and native resize cost.
+
 **Goal.** A render is cheap and predictable. The preview is fetched once per
 selection. Every number has a name.
@@ -206,4 +238,9 @@
 ## Phase 5: one file kind and one order

+Status 2026-10-18: done. [6]/[7] implement classification tables and
+adapter-owned order, including descending name order. Their old open-status
+wording below is historical. Completed implementation does not imply
+user acceptance of every related tracker entry.
+
 **Goal.** "What kind of thing is this entry?" and "in what order do entries
 appear?" are each answered in one place per side.
@@ -220,4 +257,9 @@

 ## Phase 6: a minimal server
+
+Status 2026-10-18: partly done. Steps 3, 6 and conditional step 7 are
+complete; steps 1, 2, 4 and 5 retain work. Python is 2,491 lines, with two
+function-local compatibility imports. RST and archive consumers still use
+the preview API; review old dependency/line budgets before deleting behavior.

 **Goal.** The Python server does only what a browser cannot: list a
@@ -269,4 +311,9 @@
 ## Phase 7: one test harness

+Status 2026-10-18: partly done. Steps 1, 2 and 4 are implemented;
+3 and 5 remain partial. Root pytest and both static modes pass in [99]/[101].
+No fixed waits remain. Separate browser lifecycles persist, and a root
+pytest -n auto pass is not established. Parallel CI suites do not prove it.
+
 **Goal.** One command runs every test. A failure names its check. No test
 waits for a fixed time.
@@ -294,4 +341,9 @@
 ## Phase 8: preview and editing to world class

+Status 2026-10-18: requested implementations in steps 1–4 are done.
+Registry, CSV/video/browser PPTX, RST evaluation and editor modules exist.
+Step 2's unconditional preview-API removal is overtaken by RST/VTT/archive
+consumers. Full office fidelity and safe-save work remain separate goals.
+
 **Goal.** Preview and editing are a table, not a ladder, and the table is the
 same in both editions.
@@ -314,4 +366,9 @@
 ## Phase 9: native shells

+Status 2026-10-18: prototype steps 1–3 are done. [29] supplies the model;
+[30]/ADR 0079 qualify WebKitGTK; [31]/ADR 0066 retain WebView over widgets.
+ADR 0079 records 220 UI checks passing in 4/5 runs and remaining native limits.
+This is a Linux prototype, not cross-platform application release parity.
+
 **Goal.** One native shell runs the same core with native ports.

```

## Completion checks, 2026-10-18

- The audit covers all ten phases, all 52 numbered steps and both unnumbered
  Phase 5 proposals. A mechanical coverage check found no missing step.
- Four draft texts cover Phases 0/1: two documentation slices, a CI validation
  slice retained under existing [93]/[94], and an exception-policy slice.
  Questions and dependencies are explicit; no new issue numbers were allocated.
- `uv run pytest server/tests/test_docs.py -q`: 12 passed in 0.86 s.
- `uvx pre-commit run --all-files`: all six hooks passed after the draft.
- The extracted roadmap patch passes `git apply --check` against audited main.
  It remains inside this description; docs/ROADMAP.md has no diff.
- `git diff --check` passes. Only this description and [102]'s tracker move
  change. No implementation or architecture-review file changes.
- Full-suite evidence is cited above. No full suite was rerun, and no push,
  deployment or service restart was performed. [102] completion awaits user
  acceptance and must retain `[ ]`.
