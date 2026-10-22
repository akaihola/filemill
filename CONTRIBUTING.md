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
# Root collection, split into five named evidence shards:
# keyboard:
timeout 1800 uv run pytest server/tests/test_browser_keyboard.py
# served-ui-early:
timeout 1800 uv run pytest server/tests/test_browser_new_ui.py --served-ui-part=early
# served-ui-late:
timeout 1800 uv run pytest server/tests/test_browser_new_ui.py --served-ui-part=late
# server-contracts:
timeout 1800 uv run pytest server/tests --ignore=server/tests/test_browser_keyboard.py --ignore=server/tests/test_browser_new_ui.py
# static-bundle:
timeout 1800 uv run pytest static/tests --bundle
# Additional development-mode qualification:
timeout 1800 uv run pytest static/tests --dev
(cd server && timeout 1800 uv run pytest)
# DOM-free model checks (choose one):
node ui/core/model/test.mjs
deno run --allow-read=ui/core/model ui/core/model/test.mjs
```

Evidence runs take these five shards one at a time. Together they collect
exactly the root suite. The two ignored browser files in `server-contracts`
are covered by keyboard and both served UI shards. No test is omitted.
[The partition hook] divides the served module's collection into ordered
halves, with the extra case in the early half. Each command reports the
other half as deselected; that half must run in its own command. The option
refuses other modules, and the default root collection is unchanged. The aggregate
`timeout 1800 uv run pytest` can exceed its bound on a shared host; use the
shards for complete evidence. Keep the bound at 1,800 seconds for each shard.

Compare collections after changing the shard commands. Set `TMPDIR` to a
writable temporary directory first:

```bash
uv run pytest --collect-only -q > "$TMPDIR/root-collection.txt"
uv run pytest server/tests/test_browser_keyboard.py --collect-only -q > "$TMPDIR/keyboard-collection.txt"
uv run pytest server/tests/test_browser_new_ui.py --served-ui-part=early --collect-only -q > "$TMPDIR/served-ui-early-collection.txt"
uv run pytest server/tests/test_browser_new_ui.py --served-ui-part=late --collect-only -q > "$TMPDIR/served-ui-late-collection.txt"
uv run pytest server/tests --ignore=server/tests/test_browser_keyboard.py --ignore=server/tests/test_browser_new_ui.py --collect-only -q > "$TMPDIR/server-contracts-collection.txt"
uv run pytest static/tests --bundle --collect-only -q > "$TMPDIR/static-bundle-collection.txt"
sed -n '/::/p' "$TMPDIR/root-collection.txt" | LC_ALL=C sort > "$TMPDIR/root-ids.txt"
sed -n '/::/p' "$TMPDIR/keyboard-collection.txt" "$TMPDIR/served-ui-early-collection.txt" "$TMPDIR/served-ui-late-collection.txt" "$TMPDIR/server-contracts-collection.txt" "$TMPDIR/static-bundle-collection.txt" | LC_ALL=C sort > "$TMPDIR/shard-ids.txt"
cmp "$TMPDIR/root-ids.txt" "$TMPDIR/shard-ids.txt"
```

Sorting retains duplicate IDs, so this also detects overlapping shards.
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

[the partition hook]: conftest.py
