# Contributing to Filemill

## Setup

Read the [root README] for editions and layout. Development needs Python 3.12
or newer, `uv`, Node or Deno for model checks, and Deno 2.6.8 for the quality
gate. The [workspace lockfile] selects development dependencies.

From the repository root:

```bash
uv sync
```

Install the locked Playwright browsers and their system prerequisites as
explained in the [server test guide]. Server search tests need `rg`; Git
bundle checks need `git`. Native tests have separate [native prerequisites].
Edit shared UI files through [ui/]; follow the [shared UI instructions] for
the development page, bundle rebuild and server restart.

## Model and preview boundaries

Keep browser APIs out of [ui/core/model/], including its imports. Pass measured
sizes and plain key data into model functions. Keep element creation, event
listeners and rendering effects in the adjacent browser modules. The two
browser editions and native host use the same model.

Keep source highlighting in [ui/core/markdown-source.js]. Preserve each source
character and keep links inside code inactive. Both Markdown preview modes use
[ui/core/markdown-links.js] for destination validation and path resolution.
Test link behavior with the real vendored Markdown renderer.

Read the [architecture review] before implementation. Changes to a port or
behavior need an ADR in the same change, as its [rules for changes] require.
Use red-green TDD for behavior changes. For documentation-only work, run the
checks that read the affected documents.

## Tests

Run these commands from the repository root. Run suites one at a time on a
shared host. A timeout bounds a hung test; it is not a readiness wait.

```bash
# Server and static bundle tests collected by the root configuration:
timeout 1800 uv run pytest
# Each browser edition separately:
timeout 1800 uv run pytest static/tests --bundle
timeout 1800 uv run pytest static/tests --dev
(cd server && timeout 1800 uv run pytest)
# DOM-free model checks (choose one):
node ui/core/model/test.mjs
deno run --allow-read=ui/core/model ui/core/model/test.mjs
```

Root pytest does not collect the native contract suite or run the static suite
in both modes automatically. The [native guide] gives its separate commands.
The [testing index] gives focused documentation checks and regression links.
Use [condition-based waiting] for browser readiness. Deliberate response
delays can supply slow test input.

[static/test-e2e.py] is an interactive check, requiring a folder pick and
terminal input. Use the [manual folder checklist]; do not collect it as an
automated browser test.

The [search mount regression] uses a controlled clock and delayed responses.
It checks search cancellation across local-folder mounts and restoration after return:

```bash
timeout 1800 uv run --project server pytest server/tests/test_browser_new_ui.py -k local_mode_cancels
```

## Quality gate

Install the local hook and run the gate from the repository root:

```bash
uvx pre-commit install
uvx pre-commit run --all-files
```

The [hook configuration] runs Ruff, Ruff format, mypy, Deno format, Deno lint,
the Python suppression-link guard and static bundle consistency. Each Python
`noqa` comment must link a focused issue, for example
`# noqa: F401 -- docs/tasks/24-split-app-py.md`. Remove unnecessary suppressions.
The guard scans Git-tracked Python files and ignores strings and docstrings.

Ruff infers Python 3.12 from [server/pyproject.toml]. Do not raise its target
to the local interpreter version. [CI] pins Deno to 2.6.8; use that locally.
Its lint job runs the gate and model checks. Three subsequent suite jobs run
static bundle, static development and server tests. Server CI measures branch
coverage without a percentage threshold. Only main publishes, after all jobs
pass. Local hook installation and required branch checks are separate settings;
the workflow does not establish that either is enforced for every contributor.

## Commits and completion

Use a Conventional Commit prefix: `feat:`, `fix:`, `test:`, `docs:`,
`refactor:`, `chore:`, `style:` or `perf:`. Keep each commit to one logical
change. Update the documentation in the same commit as the change.

Follow the [tracker rules] for starting work, merging and completion. Completion
uses `[ ]` in Completed / Accepted. Only user or authorized steward acceptance
changes it to `[x]`.

## Writing

Use repository-relative links, generic example hosts and disposable directories.
Do not name a developer's account, machine or private checkout. Document
environment-specific steps conditionally. Keep public project links and paths
that form part of the application contract.

Use Simplified Technical English: short sentences, common words, active voice
and one instruction per step. Define technical terms. Use reference-style links
in human documentation and inline links in agent instructions.

[root README]: README.md
[workspace lockfile]: uv.lock
[server test guide]: server/CONTRIBUTING.md#running-tests
[native prerequisites]: native/README.md#build-and-run
[ui/]: ui/
[shared UI instructions]: README.md#working-on-the-shared-ui
[ui/core/model/]: ui/core/model/
[ui/core/markdown-source.js]: ui/core/markdown-source.js
[ui/core/markdown-links.js]: ui/core/markdown-links.js
[architecture review]: docs/ARCHITECTURE-REVIEW.md
[rules for changes]: docs/ARCHITECTURE-REVIEW.md#rules-for-changes
[native guide]: native/README.md#checks
[testing index]: docs/testing/README.md
[condition-based waiting]: server/CONTRIBUTING.md#wait-for-an-element-never-for-a-duration
[static/test-e2e.py]: static/test-e2e.py
[manual folder checklist]: static/FSA-TEST-CHECKLIST.md
[hook configuration]: .pre-commit-config.yaml
[server/pyproject.toml]: server/pyproject.toml
[CI]: .github/workflows/publish.yml
[tracker rules]: TASKS.md#rules

[search mount regression]: server/tests/test_browser_new_ui.py
