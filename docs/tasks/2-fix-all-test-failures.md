---
depends-on: []
---

# Fix all test failures

`cd server && uv run pytest` on main (de104f5) gave **21 failed, 843 passed
in 13:20** (2026-09-01, full log recorded during diagnosis). Every failure has
a root cause; two are fixed here, the remaining 19 are split into their own
task.

## Failure inventory and causes

### Fixed by this task

- `tests/test_resource_routes.py::test_markdown_link_drops_hidden` — **the
  test is wrong.** Its passing siblings request `layout=no-columns`, where the
  server embeds the rendered document with rewritten links. This test used the
  default columns layout, where the server returns only the shared-UI app
  shell (1.6 kB, zero `<a>` tags) and markdown renders client-side, so the
  asserted server-side href never exists. Fix: request `layout=no-columns`
  too; the intent (rewritten links drop `hidden`) is unchanged.
- `tests/test_browser_new_ui.py::test_hidden_show_starts_with_dotfiles_visible`
  — **the code is wrong.** `ui/core/state.js` seeds `state.dotfiles` from
  `root.dataset.hidden === "show"`, but nothing sets `data-hidden`:
  `_ui_shell` in `server/src/filemill/app.py` emits
  `data-theme/density/root/filemill/layout` and stops there. `ViewState`
  deliberately excludes `hidden` (links must drop it), so the fix reads
  `hidden` from the raw request query at the `_ui_shell` call sites and passes
  it through as `data_hidden`. No ui/ change.

### Split into their own task

19 × `tests/test_browser_keyboard.py`: `test_arrow_left_keeps_browser_url_in_sync`,
`test_nested_column_navigation_keeps_root_mount_in_url`,
`test_parent_column_survives_preview_after_arrowleft_arrowright_cycle`, and
all 16 `test_mobile_*` tests.

These drive the legacy htmx column UI at `/` and wait for `window.htmx`. `/`
now serves the shared-UI shell (`index()` → `resource()` → `_ui_shell`); no
page they load references htmx, so `_wait_for_htmx` times out (30 s each)
regardless of network. This is structural, not the environmental 407-proxy
case the file's docstring describes: the CDN is reachable (direct Chromium
fetch of unpkg htmx → 200) and the failures reproduce identically with and
without a proxy. They looked green before only because `live_server` skips
the whole file when `PLAYWRIGHT_BROWSERS_PATH` is unset. They need migration
to the shared UI, not repair — too large for this change.

### Out of scope

The remembered "fold-spine count" failure lives in `static/test-ui.py`, a
separate suite outside `cd server && uv run pytest` (likely a 300 ms
animation-timing race). `test_browser_new_ui.py::test_arrow_navigation_folds_but_never_unfolds`
passes.

## Notes

- Re-runs should pin order with `-p no:randomly` (the suite uses
  pytest-randomly); never run two Playwright pytest runs in parallel on one
  host.
- No test is disabled or deselected; the suite stays red on the 19 keyboard
  tests until the migration task lands.
