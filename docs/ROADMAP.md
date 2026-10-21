# Technical roadmap

This roadmap groups progress toward the [goals]. The [architecture review]
owns the remaining findings and their remediation order. Follow that order
when it conflicts with phase numbering. Work status and acceptance live in
the [tracker]. A delivered implementation does not imply user acceptance.

## Status index, 2026-10-22

Checked against main `9c2e6128`. The [documentation review] gives code evidence
and unresolved decisions. The [earlier roadmap audit] retains the original
step-by-step audit and measurements. Old commands and removed files in that
record are history; use the [contributor guide] for current commands.

| Phase | Delivered | Remaining |
| --- | --- | --- |
| 0 | Shared finder, retired HTMX removal, root workspace, documentation and suite repairs | Clean-environment command audit (A11); keep current CI green |
| 1 | Seven local gate hooks, model checks, three CI suites and gated Pages publishing | Verify hook adoption and branch protection separately |
| 2 | Shared edition reference, central tracker, ADRs, contributor/security documents | Ongoing drift checks; unresolved document-size policy |
| 3 | ES modules, concatenating builder, DOM-free model | Full node contract; core still knows HTTP search and virtual paths |
| 4 | Preview reuse, selection model, folding model and named tuning values | Broader async ownership (A9); literal helper-size/deletion policy |
| 5 | File-kind tables and adapter-owned order | Preserve their regressions; virtual identity remains A6/A7 |
| 6 | Starlette server, vendored browser Markdown/DOCX, removed mount aliases | Source/member routing (A8), acquisition limits (A10), size/dependency policy |
| 7 | Root pytest, separate static modes, condition-based waits and test isolation repairs | Shared fixture consolidation and verified parallel execution |
| 8 | Registry, CSV, video, PPTX text, RST, editor modules and revision-checked saves | Office fidelity, local RST and remaining representation gaps |
| 9 | Qualified Linux WebKitGTK prototype | Cross-platform parity, native deletion, persistence and rich/raw integration |

## Phase 0: green and honest

Keep the shared finder as the only UI. The old HTMX finder and `no-columns`
layout are gone. The [URL contract] accepts two layouts. Preserve the repaired
JSON ordering, root-relative resources and current preview behavior.

The [architecture review] records delivered fixes, including save safety (A4),
JSON refresh (A13), bundle lifetime (A14), preview reuse, history and security
repairs. Historical green suites are evidence for their revisions. They are
not a fresh result for an arbitrary later main. A11's clean-environment
command audit is still open.

## Phase 1: gates

The [hook configuration] has Ruff, Ruff format, mypy, Deno format, Deno lint,
Python suppression links and bundle consistency. The [CI workflow] runs the
model checks too. Its static bundle, static development and server suites
must pass before main can publish. CI measures server branch coverage without
a percentage threshold. Local hook installation and branch protection remain
separate operational checks.

## Phase 2: one source of truth for documents

Use the [root README] for edition capabilities, the [usage guide] for user
behavior and settings, and the [contributor guide] for shared commands and
rules. Edition guides keep their own startup, browser or native details.
The [security policy] owns trust and mutation boundaries.

Keep the central tracker and dated decisions. Update living documents with
implementation changes. Preserve historical measurements; do not copy them
into current instructions. The under-40-line ADR policy is unresolved below.

## Phase 3: make the shared UI a module graph

The [shared model] imports without a DOM; adjacent browser modules still use
the DOM. All three entry points use ES modules. The [static builder] follows
the static import graph and concatenates it into the committed bundle.

The [port contract] documents common fields and optional capabilities,
including refresh invalidation and revision-checked writes. It does not yet
exhaust adapter-specific node fields. Core still checks `vpath` and constructs
HTTP search requests; A12 records the remaining dependency-direction work.
Do not treat the whole core as a DOM-free package.

## Phase 4: state and render discipline

[Preview rendering] now retains both pending fills and completed DOM across
resize and folding. Its key includes node, root, ports, content availability,
metadata, revision, representation and relevant settings. Editor Save and
Cancel refill it. [The reuse repair] supplies the missing guarantee.

Selection uses names and derived row indices. Folding arithmetic is in the
model; layout owns scrolling. The [tuning guard] checks named values and
reasons. Broader navigation generations and resource ownership remain A9.
`applyScroll` still coordinates extracted helpers. The original demand to
remove it is a policy question, not evidence that preview reuse is missing.

## Phase 5: one file kind and one order

Classification and adapter-owned directory order are implemented in the
[Python file-kind table], [browser file-kind table], [HTTP API] and [FSA adapter].
Shared sorting preserves provider order for default ascending names and
reverses directory/file groups for descending names. Keep the [model checks]
and served ordering regressions. Lossless virtual identity is separate A6/A7
work; these tables do not solve it.

## Phase 6: a minimal server

The server uses Starlette and Uvicorn. Markdown and DOCX render in the browser
from vendored modules. The [preview dispatcher] still handles RST and server
members; Pygments remains a runtime dependency. PPTX extraction is in the
browser and python-pptx is test-only.

Named mount and alternate shell aliases are removed. The [resource routes]
use root-relative paths, with registered API/assets taking precedence.
`--live` remains Uvicorn reload. Path checks and PWA handlers have their own
modules. Production function-local imports have been removed; the [tuning
guard] checks that too.

A8 owns the remaining representation/source separation. A10 owns acquisition
limits. Keep current supported renderers and providers while the original
server-size and dependency budgets await a decision.

## Phase 7: one test harness

Root pytest collects server tests and static tests through the [root pytest
configuration]. Static bundle is the default; development and native modes
need explicit runs. The [contributor guide] gives commands and prerequisites.
Native contracts and the interactive picker are separate checks.

Use [condition-based waiting] for readiness. The [browser-wait guard] rejects
`wait_for_timeout`; it does not ban every sleep. Delayed responses can provide
test input, but a race test must observe overlap. The earlier proxy-removal
step is delivered. Separate browser fixtures and module-level app state
remain; a root `pytest -n auto` pass is not established, and pytest-xdist is
not a declared development dependency.

## Phase 8: preview and editing to world class

The [renderer registry], browser virtual adapters and [editor modules] exist.
CSV, MP4, PPTX slide text and RST are supported as described in the [edition
reference]. RST evaluation is complete; do not repeat that experiment as
unstarted work.

Revision-checked replacement now protects ordinary stale drafts and preserves
old bytes on pre-rename failures. See the [replacement decision] for all three
hosts and its race/power-loss limits. Remaining local RST, member Source and
native Source gaps are A8. Full Office layout fidelity remains a product goal.
Deleting the preview API unconditionally would remove supported behavior.

## Phase 9: native shells

Keep the direct Linux WebKitGTK host and shared DOM renderer, as the [native
decision] specifies. Do not start another widget renderer without a new
measured case. The [native guide] gives build and qualification commands.
Its old timing and failure ratios are dated measurements, not current rates.
Preview reuse has since landed; native rich/raw integration, deletion,
remembered folders and cross-platform release parity remain future work.

## Policies awaiting a decision

The original numerical constraints are retained here pending an explicit
policy decision. They are not grounds to delete working features or evidence.
See the [open questions] for proposed answers.

- **One task per phase:** phases already span multiple issues. Use the
  architecture review's bounded remediation work; the original size claim is
  not met.
- **ADRs under 40 lines:** 24 of 91 ADR files have at least 40 lines at the
  checked revision. Measurements stay intact in this review.
- **Server under 1,500 Python lines:** 2,887 lines, including blank lines and
  comments, across all production Python files.
- **Exactly four runtime dependencies:** the old set was Starlette, Uvicorn,
  Typer and python-pptx. The declaration now has six entries: Starlette,
  Uvicorn, Typer, Pygments, docutils and conditional zstandard. Python 3.14+
  does not need the runtime zstandard package. python-pptx is test-only.
- **Layout helper constraints:** the original under-25-line helpers and
  deletion of `applyScroll` are not established. Keep the measured folding
  behavior until the policy is resolved.
- **Document/code line ratio and ten-minute onboarding:** remain goals,
  without new validation in this pass.

## How we keep it this way

Follow the architecture review's [rules for changes] and the [contributor
guide]. Keep red-green behavior tests, same-change documentation and ADRs,
and remove retired code with its replacement. A red suite blocks a merge.

Every Python suppression needs a focused issue link. A disabled test for
broken supported behavior needs an issue; a platform or optional-tool skip
needs an explicit prerequisite reason. CI must supply required prerequisites
and run applicable checks. A local run does not prove branch protection,
remote CI, deployment or user acceptance.

[goals]: GOALS.md
[architecture review]: ARCHITECTURE-REVIEW.md
[tracker]: ../TASKS.md
[documentation review]: reviews/2026-10-22-docs-review.md
[earlier roadmap audit]: tasks/102-audit-the-technical-roadmap-against-main-and-draft-the-next-phase-s-is.md
[contributor guide]: ../CONTRIBUTING.md
[URL contract]: ../server/src/filemill/urls.py
[hook configuration]: ../.pre-commit-config.yaml
[CI workflow]: ../.github/workflows/publish.yml
[root README]: ../README.md
[usage guide]: USAGE.md
[security policy]: ../SECURITY.md
[shared model]: ../ui/core/model/
[static builder]: ../static/build-index.py
[port contract]: ../ui/core/ports.js
[Preview rendering]: ../ui/core/render.js
[the reuse repair]: tasks/140-reuse-the-preview-element-across-resizes-and-folding.md
[tuning guard]: ../server/tests/test_review_conditions.py
[Python file-kind table]: ../server/src/filemill/vfs.py
[browser file-kind table]: ../ui/core/file-kind.js
[HTTP API]: ../server/src/filemill/api.py
[FSA adapter]: ../ui/adapters/fsa.js
[model checks]: ../ui/core/model/test.mjs
[preview dispatcher]: ../server/src/filemill/preview.py
[resource routes]: ../server/src/filemill/app.py
[root pytest configuration]: ../pytest.ini
[condition-based waiting]: ../server/CONTRIBUTING.md#wait-for-an-element-never-for-a-duration
[browser-wait guard]: ../server/tests/test_browser_waits.py
[renderer registry]: ../ui/core/renderers.js
[editor modules]: ../ui/editor/
[edition reference]: ../README.md#choose-an-edition
[replacement decision]: adr/0090-revision-checked-file-replacement.md
[native decision]: adr/0079-native-shell.md
[native guide]: ../native/README.md
[open questions]: reviews/2026-10-22-docs-review.md#open-questions
[rules for changes]: ARCHITECTURE-REVIEW.md#rules-for-changes
