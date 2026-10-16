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
