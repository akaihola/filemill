---
depends-on: [96]
---

# Move the CI workflows to action versions that run on Node.js 24

The workflows still use `actions/checkout@v4`, `actions/setup-python@v5`,
`astral-sh/setup-uv@v5`, `actions/upload-pages-artifact@v3` and
`actions/deploy-pages@v4`, which run on Node.js 20 and draw GitHub's deprecation
warning. palindromi.fi did the same move in its task [9] (`633892d`:
checkout@v7, upload-pages-artifact@v5, deploy-pages@v5).

- Bump each action to its current major that runs on Node.js 24; read each
  action's release notes for breaking input changes.
- Acceptance: a CI run on the change shows no Node.js 20 annotations and the same
  suites pass as before.

## Implementation plan, 2026-10-17

1. Add a failing workflow regression test for the reviewed Node.js 24 action refs.
2. Update checkout to v7, setup-python to v7, setup-uv to v10.3.0,
   upload-pages-artifact to v5 and deploy-pages to v5. Keep setup-deno at v2,
   whose current action metadata already uses node24.
3. Run the configuration tests and existing quality gates, then dispatch CI on
   the feature branch. Inspect every job's annotations for Node.js 20 warnings.
4. Rebase and merge into main, publish through the existing workflow, and mark
   the issue completed pending acceptance.

## Release compatibility review

- [checkout v5](https://github.com/actions/checkout/releases/tag/v5.0.0)
  requires runner 2.327.1 for Node.js 24. [v6](https://github.com/actions/checkout/releases/tag/v6.0.0)
  stores credentials separately; [v7](https://github.com/actions/checkout/releases/tag/v7.0.0)
  restricts unsafe fork checkouts for pull_request_target/workflow_run. This
  workflow uses hosted ubuntu-latest and ordinary pull_request/push events.
- [setup-python v6](https://github.com/actions/setup-python/releases/tag/v6.0.0)
  moves to Node.js 24 with runner 2.327.1 minimum.
  [v7](https://github.com/actions/setup-python/releases/tag/v7.0.0) removes
  pip-install, which this workflow does not use. Python remains 3.12.
- setup-uv [v6](https://github.com/astral-sh/setup-uv/releases/tag/v6.0.0)
  removes pyproject-file/uv-file and separates environment activation;
  [v7](https://github.com/astral-sh/setup-uv/releases/tag/v7.0.0) uses Node.js 24
  and removes server-url. None of these inputs are used here.
  [v8](https://github.com/astral-sh/setup-uv/releases/tag/v8.0.0) removes the old
  manifest format and stops publishing major/minor tags, so use the immutable
  [v10.3.0](https://github.com/astral-sh/setup-uv/releases/tag/v10.3.0) tag.
  [v9](https://github.com/astral-sh/setup-uv/releases/tag/v9.0.0) disables cache
  pruning by default; set prune-cache: true to retain existing cleanup.
  [v10](https://github.com/astral-sh/setup-uv/releases/tag/v10.0.0) disables
  automatic caching for sensitive events, none of which this workflow uses.
- [upload-pages-artifact v4](https://github.com/actions/upload-pages-artifact/releases/tag/v4.0.0)
  excludes hidden files. The explicit _site file list has none.
  [v5](https://github.com/actions/upload-pages-artifact/releases/tag/v5.0.0)
  uses upload-artifact v7, whose runtime is Node.js 24. The path input remains.
- [deploy-pages v5](https://github.com/actions/deploy-pages/releases/tag/v5.0.0)
  uses Node.js 24 without changes to the inputs or page_url output used here.
- [setup-deno v2.0.5](https://github.com/denoland/setup-deno/releases/tag/v2.0.5)
  includes the Node.js 24 migration within the existing v2 major.

## Validation and blocker, 2026-10-17

- Red: the new workflow regression failed on actions/checkout@v4 before the
  workflow change. Green: all nine configuration tests passed afterwards.
- Ruff lint/format, Deno format/lint, model tests and bundle freshness passed.
  Mypy passed on Python 3.13. The initial Python 3.14 run failed to resolve
  zstandard, which this project's dependency marker excludes on Python 3.14.
- Upstream action metadata confirms node24 for every JavaScript action,
  including upload-pages-artifact v5's nested upload-artifact v7 action.
- GitHub rejected the feature branch push because the configured token lacks
  workflow scope. SSH also failed with Permission denied (publickey).
  No CI run could be started, so the no-Node.js-20-annotations acceptance check
  remains unverified. Deployment and completion are pending CI access;
  issue [94] stays In Progress and user acceptance remains unchecked.
- GitHub main is still ff7b314383e7e6df2ad3e4a91bceef8cb16bd35b, before the
  local [96] history rewrite. Publishing rewritten main is explicitly reserved
  for the user in [96], so this issue does not force-push main. This is a
  separate prerequisite for the eventual main CI run and deployment.
- The full server run was interrupted after a failure in the unchanged
  test_rendered_relative_markdown_link_uses_root_relative_url browser test.
  A focused rerun reproduced it: the URL changes to the linked Markdown file
  but the preview reads "Select a file to preview" instead of "Next".
  This workflow-only change does not modify that test or application code.
  Interruption also caused a pytest tmp_path teardown KeyError, so the broad
  server attempt has no complete suite summary and is not a passing check.
  The focused test also failed identically on pre-change local main, using a
  separate Python 3.13 environment, confirming it is a baseline failure.

- Full static bundle suite: 116 passed, one existing Docutils deprecation
  warning, in 792.70 seconds.
- Full static development suite: 116 passed, one existing Docutils deprecation
  warning, in 818.37 seconds.

## Local delivery

Rebased onto local main and merged locally after the workflow regression,
quality checks and both static suites passed. The server baseline failure
above remains outside this issue. No GitHub ref was updated, no CI run was
started and no deployment was performed. Issue [94] remains In Progress until
its GitHub CI acceptance check can be completed.

## Completion follow-up, 2026-10-19

The rewritten history is now published. The first main run was at `a0bfd95`. Its
[publish run 39292689552](https://github.com/akaihola/filemill/actions/runs/39292689552)
passed lint without Node.js 20 annotations. Both static suites failed keyboard
scrolling and refresh; the server suite failed the parent-column URL check.
Publishing was skipped.

The follow-up plan is to reproduce each failure, add focused regressions,
repair the causes, run the quality gates, then push and verify all CI jobs
and the Pages deployment before completing this issue.

- Delaying the leaf preview by twelve animation frames reproduced the
  PageDown timeout. Wait for the actual scrollable content before the key.
- The refresh failure reproduced locally. Mounting during a fold left the
  root hidden. A focused mount test failed with `folded === 1`; another test
  showed a deferred glide overriding a later instant move (`dial() === 125`).
  Keep the scroll writer in layout, cancel superseded callbacks and reset the
  dial on root mount. See [ADR 0084](../adr/0084-new-fold-moves-cancel-older-glides.md).
- The server test can capture the previous folder URL while the selected
  directory is still loading. Wait for the expected URL before recording it.
  Keep the column, selection and URL equality assertions.

GitHub completion and deployment verification are pending this follow-up.

The first full local check passed both static modes (156 tests each). The
server run had 938 passes and one failure: the new reset delayed the initial
widening range until the settle timer. A focused immediate-range regression
also failed with `dial() === 0` after a leftward fling. The layout reset now
clears that timer, so the first render establishes the range immediately.
The existing server widening test and the new regression must both pass.

The first follow-up GitHub run also exposed the same measurement race in
`test_geometry_changes_preserve_preview_rules[mouse]` in both static modes:
the scroll position reached its target before the scroll event updated the
columns. Wait for the expected fold count before measuring preview geometry.
Keep the existing preview-width assertion.
