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

### Split into their own task (done: ported to the shared UI)

19 × `tests/test_browser_keyboard.py`: `test_arrow_left_keeps_browser_url_in_sync`,
`test_nested_column_navigation_keeps_root_mount_in_url`,
`test_parent_column_survives_preview_after_arrowleft_arrowright_cycle`, and
16 of the 24 `test_mobile_*` tests.

These drove the legacy htmx column UI at `/` and waited for `window.htmx`. `/`
now serves the shared-UI shell (`index()` → `resource()` → `_ui_shell`); no
page they loaded references htmx, so `_wait_for_htmx` timed out (30 s each)
regardless of network. This was structural, not the environmental 407-proxy
case the file's docstring describes: the CDN is reachable (direct Chromium
fetch of unpkg htmx → 200) and the failures reproduced identically with and
without a proxy. They looked green before only because `live_server` skips
the whole file when `PLAYWRIGHT_BROWSERS_PATH` is unset.

The migration subtask ported each test's intent to the shared UI, following
`tests/test_browser_new_ui.py`. The URLs lost their `/f/<mount>` prefix (on
`/` the path *is* the root-relative file path), ← moves focus without closing
columns, and the mobile "scroll to reveal" intent maps onto the fold dial:
`scrollLeft` condenses left columns to spines (`ui/core/layout.js`), so "the
scroll fired" became "the dial engaged", "minimal scroll" became layout()'s
least-folding target, and taps unfold a folded column first — the gesture the
UI itself advertises. The 8 `test_mobile_*restore*` tests, plus
`test_legacy_query_url_canonicalizes_after_nested_navigation` and
`test_rendered_relative_markdown_link_uses_root_relative_url`, keep driving
the htmx shell at `/f/`, which still serves it — so the htmx/proxy plumbing
in the file stays until `/f/` goes away.

### Out of scope

The remembered "fold-spine count" failure lives in `static/test-ui.py`, a
separate suite outside `cd server && uv run pytest` (likely a 300 ms
animation-timing race). `test_browser_new_ui.py::test_arrow_navigation_folds_but_never_unfolds`
passes.

## Notes

- Re-runs should pin order with `-p no:randomly` (the suite uses
  pytest-randomly); never run two Playwright pytest runs in parallel on one
  host.
- No test is disabled or deselected; with the 19 keyboard tests ported the
  whole suite is green (`cd server && uv run pytest -p no:randomly`).
- Re-verified on `main` @ 85ffe6d (2026-09-02), with
  `PLAYWRIGHT_BROWSERS_PATH` set so no browser test was skipped:
  **870 passed in 270 s** for the suite, and **31 passed in 130 s** for
  `tests/test_browser_keyboard.py` alone — 21 of those 31 now drive the
  shared UI at `/`, the other 10 the `/f/` shell that is still served.
