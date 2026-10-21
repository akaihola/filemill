# Documentation review, 2026-10-22

Reviewed main `9c2e612869d8e127b152c61c029781164a61615c`. Work began on
2026-10-21 and continued after local midnight. This is the [documentation
audit task]. The [architecture review] was read first and remains unchanged.
This pass corrects living prose; it changes no application code or tests.

## Coverage and method

Read the complete [root README], [agent instructions], [contributor guide],
[security policy], [goals], [roadmap] and both existing files in
[docs/testing/]: the [historical test record] and all 256 rows of its
[failure inventory]. Also read the server guides, static instructions, native
guide, adapter guide, all 91 ADR files, test configuration, CI and local hooks.
Both ADRs numbered 0068 were included by filename.

Traced startup and environment claims to [server/src/filemill/cli.py], [server/src/filemill/env.py], [server/src/filemill/app.py] and
[server/src/filemill/mutations.py]; settings to [server/src/filemill/ui/core/settings.js], [server/src/filemill/ui/core/model/state.js], [server/src/filemill/ui/core/sort.js],
[server/src/filemill/ui/core/dom-renderer.js] and [server/src/filemill/ui/adapters/preview-rich.js]. Traced layouts, renderers, virtual
files, saves, worker behavior and native limits to the sources linked below.
Commands were compared with configuration and entry points. This was not a
clean-machine execution of every advertised command or a new browser/native
qualification. No external service availability or current remote CI state
was inferred from historical results.

ADRs, task descriptions, earlier reviews, the historical test inventory and
released changelog entries remain unchanged. The tracker start/completion
moves are the required workflow exception to the content scope.

## Changes by document

- **Root README:** shortened the entry point and kept one browser-edition
  capability table. Linked usage, settings, tests and native details instead
  of repeating them. Added CSV, explicit native limitations and the static
  worker caveat. Startup matches `main()` in [server/src/filemill/cli.py]; shared sources and
  assets match `_ui_shell` and versioning in [server/src/filemill/app.py], [static/build-index.py]
  and the [package configuration]. Renderer differences match [server/src/filemill/ui/adapters/app-fsa.js],
  [server/src/filemill/ui/adapters/app-http.js], [server/src/filemill/ui/adapters/preview-rich.js] and [server/src/filemill/ui/adapters/app-native.js]. Search/Git prerequisites
  match [server/src/filemill/api.py] and [server/src/filemill/providers/gitbundle.py].
- **Agent instructions:** linked the tracker, architecture baseline and
  contributor entry point. Kept TDD and scoped architecture updates. The
  test/gate pointer now leads to commands matching [pytest.ini], the
  [hook configuration] and [CI workflow], instead of leaving those entry
  points undiscoverable.
- **Contributor guide:** centralized suite/model/gate commands, prerequisites,
  writing and completion rules. Root collection covers server and static
  bundle, not every native or static mode. Evidence: [pytest.ini], [root
  fixtures], [static fixtures], both [workspace configuration] and [package
  configuration], the [hook configuration], [CI workflow] and [model checks].
  Removed duplicated per-feature test prose in favor of the testing index.
- **Security policy:** corrected the root boundary to include direct-root
  bookmarks, clarified that Open Folder retains local write capabilities,
  and specified cache eligibility and 502–504 fallback. Evidence:
  `resolve_safe` in [server/src/filemill/paths.py], `mount` in [server/src/filemill/ui/adapters/app-http.js], optional writes in
  [server/src/filemill/ui/adapters/http.js], and `network`, `asset`, `keepable` and cache limits in the
  [server worker]. Existing authorization and revision-replacement guarantees
  match [server/src/filemill/mutations.py], [server/src/filemill/api.py] and [server/src/filemill/ui/editor/editor.js].
- **Goals:** distinguished targets from shipped behavior. Qualified native
  status, offline functionality, deep links, bookmark zones, reserved routes
  and consent. Replaced the weaker decision-timing sentence with the existing
  same-change ADR rule. Evidence: [server/src/filemill/ui/adapters/app-native.js], [native adapter],
  [server/src/filemill/ui/adapters/preview-rich.js], the [server worker], [static worker], [server/src/filemill/paths.py],
  [server/src/filemill/app.py] and the name-based [deep-link model]. The ten-minute setup target
  remains unmeasured. Policy questions below remain explicit.
- **Roadmap:** replaced repeated historical implementation instructions with
  current phase summaries and linked evidence. Marked preview reuse,
  revision-checked saves, JSON invalidation, bundle ownership, function-local
  import cleanup and native qualification as delivered. Evidence: retained
  `previewCache` in [server/src/filemill/ui/core/render.js], `save` in [server/src/filemill/api.py], [server/src/filemill/ui/editor/editor.js], `invalidate`
  in [server/src/filemill/ui/adapters/vfs-json.js], retained repository owners in [server/src/filemill/providers/gitbundle.py], the
  [review-condition tests], [native host] and [native decision]. Current
  gates and collection match the [CI workflow] and [pytest.ini]. Preserved
  unresolved numerical policies instead of silently replacing them.
- **Usage guide:** moved the root README's navigation, preview, heading,
  JSON-refresh and copying detail behind one link. Added a settings/defaults
  table matching [server/src/filemill/ui/core/settings.js], [server/src/filemill/ui/core/dom-renderer.js], [server/src/filemill/ui/core/model/state.js], [server/src/filemill/ui/core/sort.js],
  [server/src/filemill/ui/adapters/preview-rich.js] and [server/src/filemill/ui/adapters/storage.js]. Behavior matches [server/src/filemill/ui/core/layout.js],
  [server/src/filemill/ui/core/nav.js], [server/src/filemill/ui/core/render.js], [server/src/filemill/ui/adapters/vfs-json.js], [server/src/filemill/ui/adapters/vfs-doc.js], [server/src/filemill/urls.py] and [server/src/filemill/ui/editor/editor.js].
  The guide names Source limitations and draft-discard behavior explicitly.
- **Server README:** qualified dotfiles as private-mode behavior, centralized
  security detail, and clarified runtime prerequisites and environment
  lookup. Explicit bind wins over the environment default; nonempty new
  variables precede legacy names. `FILEMILL_LIVE` has a writer but no reader.
  `window.FILEMILL_CDN` is a browser map, not an environment setting. Evidence:
  [server/src/filemill/cli.py], [server/src/filemill/env.py], `_ui_shell` in [server/src/filemill/app.py], [server/src/filemill/mutations.py], [server/src/filemill/api.py] and
  [server/src/filemill/providers/gitbundle.py]. The root/port/live argument table was already correct.
- **Server contributor guide:** removed duplicated shared rules and corrected
  the claim that core never sees virtual paths. Marked A4 resolved and A5
  static-only. Qualified no-build as the development path, added Firefox to
  the browser prerequisites, dated timing claims, and corrected completion
  sequencing. Evidence: `openRowMenu` in [server/src/filemill/ui/core/render.js], [server/src/filemill/ui/core/search.js], [server/src/filemill/api.py],
  both workers, [static/build-index.py], the Firefox parameterization in
  [served UI tests], [CI workflow] and the [tracker rules]. The source map
  is now explicitly selective; mutation middleware includes all-route Host
  checks in [server/src/filemill/mutations.py].
- **Static agent guide:** removed nonexistent core JSONL and preview-HTTP
  modules and the duplicate rich-preview entry. Their code is in
  [server/src/filemill/ui/adapters/vfs-json.js] and [server/src/filemill/ui/adapters/app-http.js]. Corrected publishing triggers to match the
  [CI workflow] and the claim that only the manual suite writes fixtures:
  [static URL tests] write OPFS and [native tests] write temporary roots.
- **Native guide:** dated the old binary size and one-in-five failure rate
  to their qualification run. The host still uses the same native ports in
  [native host] and [native adapter], while [server/src/filemill/ui/core/render.js] now retains preview
  DOM and pending work. No new native failure rate is claimed.
- **Adapter guide:** replaced the duplicate edition table with a link and
  kept wiring/contract details. Corrected the claims that local-folder mode
  loses no fidelity and that every virtual Source request shows source.
  Evidence: `withRichPreview` and `withServerVirtualPreview` in [server/src/filemill/ui/adapters/app-http.js],
  `member_preview_response` in [server/src/filemill/api.py], [server/src/filemill/ui/adapters/app-native.js], the [port contract]
  and [renderer registry].
- **Testing index:** added a current entry point without rewriting the
  historical record. Its commands and collection boundaries match
  [pytest.ini], [documentation tests], [review-condition tests] and
  [static fixtures]. The old TSV has 256 records plus a header; its renamed
  nodes are not a current runnable suite or skip list.
- **This review:** records the source evidence, remaining uncertainty and
  drafts. Reference-style links in human guides point to repository files;
  agent instructions keep inline links. No private machine or home paths
  were added.

## ADRs with unmarked drift

The following records have no supersession note covering the identified
divergence. Their files are unchanged. A stale consequence is distinguished
from an actual decision mismatch.

- **ADR 0041, port separation:** [The port decision] records the boundary; the three-port design remains, but its
  source-independent core claim is not fully followed. [server/src/filemill/ui/core/search.js] constructs
  and fetches `/api/search` directly; [server/src/filemill/ui/core/render.js] checks `vpath` for delete
  eligibility. The [port contract]'s opening claim repeats the same gap.
  Evidence agrees with A12. Proposed answer: keep the intended boundary and
  repair the coupling within that finding, without inventing a general plugin
  system. The new adapter guide describes the current leak.
- **ADR 0072, member Source:** [archive decision] says every highlighted
  member receives colored source. `withServerVirtualPreview` in [server/src/filemill/ui/adapters/app-http.js]
  sends no representation parameter. `member_preview_response` in [server/src/filemill/api.py]
  calls `render_preview` in [server/src/filemill/preview.py], which renders RST and HTML rather
  than calling `render_source`. Proposed answer: preserve Source semantics
  and repair the representation routing under A8, then amend the ADR in that
  behavior change. The earlier partial supersession in [ADR 0037] already
  records server highlighting, but does not resolve this mismatch.
- **ADR 0079, stale consequence:** [native decision] still says every
  render rebuilds the preview. The host selection decision remains followed;
  [server/src/filemill/ui/core/render.js] now reuses it. Its measurements remain historical. Proposed
  answer: add a dated status note in a later authorized ADR update, preserving
  the measurements and avoiding a claim of new WebKit performance results.
- **ADR 0081, stale consequences:** [mutation decision] still says saves
  are non-atomic and lack conflict checks, and treats server caching as open
  A5 work. [server/src/filemill/api.py], [server/src/filemill/app.py], [server/src/filemill/ui/editor/editor.js], the [server worker] and
  [server/src/filemill/ui/adapters/server-status.js] implement the later [replacement decision] and [offline
  decision]. Authorization itself remains followed. Proposed answer: cross-link
  those later decisions and retain the original threat-model history.
- **ADR 0086, stale consequence:** [glide decision] still calls preview
  reuse remaining A9 work. `previewCache` in [server/src/filemill/ui/core/render.js] implements it; broader
  async ownership is still open. Proposed answer: date that partial resolution
  without altering the glide-cancellation decision.
- **ADR 0087, conflicting mutation text:** [public-mode decision]'s older
  Decision paragraph says authorized hidden mutations get 404, while its
  updated Consequences points to unconditional public-write refusal.
  `authorized` in [server/src/filemill/mutations.py] returns false for public instances before
  paths/body reads, so they get 403. Proposed answer: align the earlier
  paragraph with the later [mutation decision]; keep hidden *read* refusals
  at 404. Its routing supersession note covers removed aliases, not this text.

Already marked supersessions and scope updates, including ADRs 0001–0003,
0005, 0021, 0025, 0034–0040, 0062–0066, 0069 and 0076, were considered before
listing drift. Old measurements and filenames alone were not treated as
unimplemented decisions.

## Open questions

- **Q1 — What counts as network consent?** The goals prohibit network use
  without consent. [server/src/filemill/ui/adapters/preview-rich.js] defaults its opt-out switch on;
  rendered documents can fetch images independently of it. The existing
  [consent decision] intentionally scopes the switch to renderer downloads.

  **Recommendation:** define consent separately for application delivery,
  renderer downloads and document resources. Keep the current behavior stated
  accurately until the product owner chooses whether any must become opt-in.
- **Q2 — Which roadmap budgets remain useful?** Main has 2,887 production
  Python lines, six declared runtime dependencies and 24 of 91 ADRs at least
  40 lines long. Counts include comments/blank lines and the conditional
  zstandard dependency. Function-local production imports are now zero.
  The old exact dependency set includes test-only python-pptx. `applyScroll`
  remains the measured layout coordinator. One task per phase is also unmet.

  **Recommendation:** decide these constraints explicitly. Prefer bounded
  changes, documented dependency reasons and measured behavior over deleting
  supported functionality to meet historical counts. The roadmap retains the
  old policies and their failed checks pending that decision.
- **Q3 — What does the native resize repair prove?** [server/src/filemill/ui/core/render.js] avoids
  refetching and recreating the pane, but WebKit can still reflow retained DOM
  at a new width. [native decision] measured old code and different runs.

  **Recommendation:** retain dated measurements and run a focused native
  resize qualification before claiming a new latency or reliability result.
  Keep this under A9; do not reopen shell selection.
- **Q4 — Does “a section cannot be copied” mean its name?** [document decision] excludes section copying alongside editing/deletion.
  `openRowMenu` in [server/src/filemill/ui/core/render.js] offers name and path copying for every node,
  including section nodes created by [server/src/filemill/ui/adapters/vfs-doc.js]. There is no file-duplication
  operation to compare with that sentence.

  **Recommendation:** clarify the ADR as prohibiting file mutation or
  duplication of a slice, while retaining name/link copying. Do not remove a
  useful UI action based on the ambiguous wording.
- **Q5 — Is the command audit complete?** The tests exercise selected
  documentation and command collection. They do not prove a clean install,
  ten-minute onboarding, browser system packages, native packaging, every
  manual command, or remote deployment. A11 still owns that larger audit.

  **Recommendation:** keep A11 open and run each documented command with
  explicit prerequisites in a clean environment. This review is not its
  acceptance evidence.

## Validation

Discovery used `grep` and `rg` for Markdown paths and file reads in tracked
tests. The repository-document readers are [documentation tests] and
[review-condition tests]. Other matches read generated Markdown fixtures;
browser suites are not required for this prose-only change.

The unchanged baseline passed **33 tests** with:

```bash
timeout 600 uv run --project server pytest -q server/tests/test_docs.py server/tests/test_review_conditions.py
```

After the prose changes, the same **33 tests passed** again. The full
`uvx pre-commit run --all-files` gate passed all seven hooks: Ruff, Ruff
format, mypy, Deno format, Deno lint, suppression links and bundle consistency.
A separate link check verified **359 local destinations**, reference
definitions and heading fragments across **14 changed Markdown files**. `git diff --check` passed. Browser/native suites, clean-environment onboarding
and external deployment are outside this run's validation.

## Draft issues

These are proposals for the steward, not filed issues.

- **Correct bind help precedence.** `main()` in [server/src/filemill/cli.py] says its bind address
  is “overridden by FILEMILL_BIND”, but the variable supplies only the default;
  an explicit `--bind` wins. The server README now matches execution. Change
  the CLI help with a focused regression. This needs a code change and is
  outside this documentation-only issue.
- **Reconcile unmarked ADR drift.** Add dated notes or corrections for the
  records above after deciding Q4. Preserve decisions still followed and all
  measurements. For port/source behavior, use existing A12/A8 work rather
  than creating duplicate implementation issues.
- **Decide consent and roadmap constraints.** Resolve Q1/Q2 before rewriting
  their policies or cutting features to satisfy old budgets. This is a product
  and engineering-policy decision, not a prose correction.
- **Attach remaining validation to existing work.** Q3 belongs to A9 and Q5
  to A11. Record fresh native and clean-environment results there; do not
  infer completion from this audit. Existing A5–A10 implementation findings
  remain owned by the architecture review.

[documentation audit task]: ../tasks/146-check-filemill-s-readme-contributor-docs-goals-and-roadmap-against-cur.md
[architecture review]: ../ARCHITECTURE-REVIEW.md
[root README]: ../../README.md
[agent instructions]: ../../AGENTS.md
[contributor guide]: ../../CONTRIBUTING.md
[security policy]: ../../SECURITY.md
[goals]: ../GOALS.md
[roadmap]: ../ROADMAP.md
[docs/testing/]: ../testing/
[historical test record]: ../testing/remaining-red-tests.md
[failure inventory]: ../testing/remaining-red-tests.tsv
[server/src/filemill/cli.py]: ../../server/src/filemill/cli.py
[server/src/filemill/env.py]: ../../server/src/filemill/env.py
[server/src/filemill/app.py]: ../../server/src/filemill/app.py
[server/src/filemill/mutations.py]: ../../server/src/filemill/mutations.py
[server/src/filemill/ui/core/settings.js]: ../../ui/core/settings.js
[server/src/filemill/ui/core/model/state.js]: ../../ui/core/model/state.js
[server/src/filemill/ui/core/sort.js]: ../../ui/core/sort.js
[server/src/filemill/ui/core/dom-renderer.js]: ../../ui/core/dom-renderer.js
[server/src/filemill/ui/adapters/preview-rich.js]: ../../ui/adapters/preview-rich.js
[static/build-index.py]: ../../static/build-index.py
[package configuration]: ../../server/pyproject.toml
[server/src/filemill/ui/adapters/app-fsa.js]: ../../ui/adapters/app-fsa.js
[server/src/filemill/ui/adapters/app-http.js]: ../../ui/adapters/app-http.js
[server/src/filemill/ui/adapters/app-native.js]: ../../ui/adapters/app-native.js
[server/src/filemill/api.py]: ../../server/src/filemill/api.py
[server/src/filemill/providers/gitbundle.py]: ../../server/src/filemill/providers/gitbundle.py
[pytest.ini]: ../../pytest.ini
[hook configuration]: ../../.pre-commit-config.yaml
[CI workflow]: ../../.github/workflows/publish.yml
[root fixtures]: ../../conftest.py
[static fixtures]: ../../static/tests/conftest.py
[workspace configuration]: ../../pyproject.toml
[model checks]: ../../ui/core/model/test.mjs
[server/src/filemill/paths.py]: ../../server/src/filemill/paths.py
[server/src/filemill/ui/adapters/http.js]: ../../ui/adapters/http.js
[server worker]: ../../server/src/filemill/static/sw.js
[static worker]: ../../static/sw.js
[server/src/filemill/ui/editor/editor.js]: ../../ui/editor/editor.js
[native adapter]: ../../ui/adapters/native.js
[deep-link model]: ../../ui/core/model/deeplink.js
[server/src/filemill/ui/core/render.js]: ../../ui/core/render.js
[server/src/filemill/ui/adapters/vfs-json.js]: ../../ui/adapters/vfs-json.js
[review-condition tests]: ../../server/tests/test_review_conditions.py
[native host]: ../../native/webview/main.c
[native decision]: ../adr/0079-native-shell.md
[server/src/filemill/ui/adapters/storage.js]: ../../ui/adapters/storage.js
[server/src/filemill/ui/core/layout.js]: ../../ui/core/layout.js
[server/src/filemill/ui/core/nav.js]: ../../ui/core/nav.js
[server/src/filemill/ui/adapters/vfs-doc.js]: ../../ui/adapters/vfs-doc.js
[server/src/filemill/urls.py]: ../../server/src/filemill/urls.py
[server/src/filemill/ui/core/search.js]: ../../ui/core/search.js
[served UI tests]: ../../server/tests/test_browser_new_ui.py
[tracker rules]: ../../TASKS.md#rules
[static URL tests]: ../../static/tests/test_url.py
[native tests]: ../../native/test_host.py
[port contract]: ../../ui/core/ports.js
[renderer registry]: ../../ui/core/renderers.js
[documentation tests]: ../../server/tests/test_docs.py
[archive decision]: ../adr/0072-archives-browse-by-their-members.md
[server/src/filemill/preview.py]: ../../server/src/filemill/preview.py
[ADR 0037]: ../adr/0037-syntax-highlighting-in-the-page-core-syntax-js-not-from-pygments-or-a-.md
[mutation decision]: ../adr/0081-authorize-server-mutations.md
[server/src/filemill/ui/adapters/server-status.js]: ../../ui/adapters/server-status.js
[replacement decision]: ../adr/0090-revision-checked-file-replacement.md
[offline decision]: ../adr/0089-an-offline-server-shows-older-copies-with-an-indicator.md
[glide decision]: ../adr/0086-new-fold-moves-cancel-older-glides.md
[public-mode decision]: ../adr/0087-a-public-instance-never-lists-or-serves-hidden-paths.md
[consent decision]: ../adr/0036-but-behind-a-remembered-switch-defaulting-on.md
[document decision]: ../adr/0070-documents-browse-by-headings.md
[The port decision]: ../adr/0041-core-adapters-three-ports.md
