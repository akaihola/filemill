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
