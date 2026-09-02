---
depends-on: []
---

# Show version and Git commit hash in the settings menu

Add an About group at the bottom of the settings popover showing
`Filemill <version>`, with ` · <short hash>` appended when a commit hash is
available.

## Design

- **Version**: one constant string in the popover markup in `ui/core/shell.js`.
  Shared by the static build, the dev page, and the server shell — no build
  step. A server test guards drift against `server/pyproject.toml`.
- **Commit hash**: the server already passes config to the client as `<html>`
  data attributes (`data_root`, `data_filemill`, …) in `_ui_shell()`. Add
  `data_commit`, populated once at import via
  `git -C <package dir> rev-parse --short HEAD` (all failures → empty →
  attribute omitted). `shell.js` reads `document.documentElement.dataset.commit`
  and appends the hash when present.
- **Static build**: no `data-commit` on `<html>` → version alone. No hash is
  baked into generated artifacts, so `build-index.py --check` doesn't churn
  per commit.
