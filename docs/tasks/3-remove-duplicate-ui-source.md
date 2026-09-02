---
depends-on: []
---

# Get rid of duplicate vendored code

`ui/` and `server/src/filemill/ui/` held byte-identical copies of the same
frontend — 26 duplicated files, kept in step by `server/tools/sync-ui.py` and a
CI `--check` step. Now there is one set of files: they live in the package, and
`ui/` is a symlink to it.

## Why the copy existed, and why the symlink goes this way round

A wheel cannot reach outside its own package directory, so
`_UI_DIR = Path(__file__).parent / "ui"` (`server/src/filemill/app.py`) has to
resolve inside `filemill/`. That is the whole reason a second copy was ever
made.

The obvious fix — symlink `server/src/filemill/ui` at the repo-root `ui/` —
does not work. `uv_build` refuses a symlink inside the package:

```
Error: Unsupported file type FileType { .. is_symlink: true }: src/pkg/ui
```

So the direction is forced: the real files move into the package, and the
repository root points at them.

## What changed

- All 29 files now live in `server/src/filemill/ui/`; `ui/` is a symlink to it
  (one tracked entry, mode `120000`).
- `server/tools/sync-ui.py` deleted, along with the "The packaged copy matches
  ui/" step in `.github/workflows/publish.yml`.
- `server/pyproject.toml` gained a `[tool.uv.build-backend] wheel-exclude` for
  the three adapters the static edition alone uses — `app-fsa.js`,
  `preview-rich.js`, `router-hash.js`. This replaces `sync-ui.py`'s 26-entry
  `WANTED` allow-list with three exclusions and keeps the wheel's contents
  exactly what they were.

Keeping `preview-rich.js` out of the wheel is load-bearing: it lazy-loads a
renderer from a CDN, and `test_nothing_is_fetched_from_a_cdn` exists to catch
that. It is now excluded at build time rather than never copied.

`static/index-dev.html`, `static/build-index.py` and the static test suites were
not touched — they reference `../ui/`, which still resolves.

## Verification

Measured on the rebased branch, against a wheel built from `main` at the same
commit so the comparison isolates this change:

- The wheel carries the same 26 `filemill/ui/` files as one built from `main`,
  byte for byte, with one deliberate exception: `adapters/README.md`, whose
  wording this change updates. The sdist still contains all three excluded
  adapters, so the source distribution is not lossy.
- Installing that wheel into a clean venv serves the UI: `/ui/core/ports.js`,
  `/ui/core/styles.css`, `/ui/adapters/app-http.js` and `/ui/vendor/seti.woff`
  all return 200, the three excluded adapters return 404, and the `/n/` shell
  renders referencing `/ui/core/shell.js`. `ui/` is a real directory there, not
  a symlink — the link exists only in the repository.
- `static/build-index.py --check` green at 211,523 bytes, the same size `main`
  produces: the symlink is transparent to the bundler.
- `cd server && uv run pytest`: 870 passed, 0 failed.
- `static/test-ui.py` 137 passed in both bundle and `--dev` mode, `test-url.py
  --dev` 15 passed. The `--dev` runs are what exercise the symlink, since they
  load `../ui/` directly, and they match the bundle exactly.
- `static/test-rich.py --dev` is 13 passed, 2 failed. Both are the offline
  fallback checks, pre-existing and unrelated — see the `test-rich` item in
  `TASKS.md`.

## Note for whoever reads TASKS.md next

The first backlog item — "Migrate the 19 legacy htmx browser tests in
`server/tests/test_browser_keyboard.py` … they fail structurally" — appears to
be stale. A full `uv run pytest` on `main` @ b96d84e during this task returned
**867 passed, 0 failed** in under four minutes, with no failures in that file.
`docs/tasks/2-fix-all-test-failures.md` says as much in its closing note. Left
in place rather than moved, since verifying and retiring it belongs to whoever
owns that item.

## Caveat

A checkout needs symlink support. That is the default everywhere except Windows
without developer mode, where `ui/` materialises as a text file and the static
dev entry point breaks.
