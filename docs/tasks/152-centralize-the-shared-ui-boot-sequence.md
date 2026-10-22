Steward issue, 2026-10-22 07:16 refill (steward decisions D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Estimated 1 h.

This is draft D3 of [the 2026-10-22 architecture review], filed as written there; read that draft and the finding it cites before starting. The review's line numbers refer to the commit it names; recheck them on current `main`.

## Work

Replace the three identical initialization blocks (server, browser-owned and native hosts) with one core initializer; leave host-specific choices at the three call sites. Remove the narration about the retired classic-script loading order.

## Acceptance

- One implementation of the seven-call sequence; each host calls it once after creating its shell.
- Mount, keyboard, sorting and preview checks keep their behaviour; check the static development and bundle builds and the native composition through their existing entry points, rebuild the static bundle and keep its import and collision checks.
- No configuration class, event bus or host inheritance tree is added.

## Ground rules

- Behaviour stays the same unless the acceptance below says otherwise. Write the failing or pinning test first where the draft asks for one.
- Run at most one focused test command at a time, under your launch prompt's memory rule; no full browser suite.
- Keep private paths and host names out of committed files (the docs tests reject them).
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker].

## Implementation, 2026-10-22

- Rechecked F3 against current main. All three compositions still had the same
  seven-call sequence.
- Added [the core initializer]. Each host calls `initCore()` once at its
  existing boot point, after the entry module creates the shell. Renderer
  registration, ports, welcome screens, persistence and mounting stay in the
  host compositions.
- Removed retired classic-script narration from both browser compositions
  and settings. Rebuilt [the static bundle] with the existing builder;
  unsupported-import and declaration-collision checks remain active.
- Added [the boot contract test] before implementation. It failed because
  the initializer did not exist, then passed after extraction. It pins call
  order, one shared implementation, one call per host and shell-first entries.
- Updated the architecture finding and adapter guide. No port or behavior
  changes were made, so the ADR rule does not require a new decision.

## Validation

- Development entry: 15 focused checks passed, including the boot contract.
- Rebuilt bundle entry: the same 14 browser checks passed.
- Native build: passed through the documented build entry. Eleven focused
  contract and shared UI checks passed through the actual embedded WebView.
- Server entry, boot contract, documentation and review conditions: 42 checks
  passed, including keyboard behavior, Markdown preview, name/metadata sorting,
  local mount search cancellation and returning to the served root.
- All seven pre-commit hooks passed, including bundle consistency, import
  restrictions and declaration collisions. The first gate run found only
  Markdown formatting in the adapter guide; formatting was corrected and
  the whole gate passed on rerun. DOM-free model checks also passed.
- Full browser suites were intentionally excluded by the task's ground rules.

## Guarded commands

Commands ran one at a time with a 1,800-second timeout. The guard checked host
memory and swap every second. All had **started at once** admission, with
0.0 seconds of waiting; none used fallback admission or stopped while running.
Values below are MiB. Swap growth is measured from each command's start.
The red test's exit 1 was expected. The first gate's exit 1 was the formatting
failure corrected above. Every subsequent acceptance check finished with exit 0.

| Command | Outcome | Wait (s) | Admission | Final | Start swap | Swap growth | Elapsed (s) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | started at once | 0.0 | 2637 | 2531 | 2474 | +12 | 8.1 | exit 1 |
| C2 | started at once | 0.0 | 2582 | 2352 | 2485 | +0 | 4.1 | exit 0 |
| C3 | started at once | 0.0 | 2670 | 2671 | 2484 | +0 | 1.0 | exit 0 |
| C4 | started at once | 0.0 | 2737 | 2397 | 2483 | +2 | 75.2 | exit 0 |
| C5 | started at once | 0.0 | 2343 | 2332 | 2484 | -38 | 55.2 | exit 0 |
| C6 | started at once | 0.0 | 2449 | 2387 | 2446 | +8 | 16.0 | exit 0 |
| C7 | started at once | 0.0 | 2441 | 2797 | 2453 | +189 | 97.2 | exit 0 |
| C8 | started at once | 0.0 | 2799 | 2545 | 2642 | -9 | 30.1 | exit 0 |
| C9 | started at once | 0.0 | 2661 | 2695 | 2633 | -7 | 14.0 | exit 1 |
| C10 | started at once | 0.0 | 2698 | 2730 | 2620 | +0 | 3.0 | exit 0 |
| C11 | started at once | 0.0 | 2727 | 2721 | 2620 | +0 | 1.0 | exit 0 |

- **C1:**

  ```bash
  uv run --project server pytest -q server/tests/test_ui_boot.py
  ```

- **C2:**

  ```bash
  uv run --project server pytest -q server/tests/test_ui_boot.py
  ```

- **C3:**

  ```bash
  python3 static/build-index.py
  ```

- **C4:**

  ```bash
  uv run --project server pytest -q server/tests/test_ui_boot.py static/tests/test_ui.py --dev -k 'ordered_core_initializer or keyboard_vertical or keyboard_horizontal or sort_options or test_preview or new_root_has_its_widening_range_immediately or test_settings'
  ```

- **C5:**

  ```bash
  uv run --project server pytest -q static/tests/test_ui.py --bundle -k 'keyboard_vertical or keyboard_horizontal or sort_options or test_preview or new_root_has_its_widening_range_immediately or test_settings'
  ```

- **C6:**

  ```bash
  nix-shell native/shell.nix --run 'python3 native/webview/build.py'
  ```

- **C7:**

  ```bash
  nix-shell native/shell.nix --run 'uv run --project server pytest -q native/test_host.py::test_native_ports native/test_host.py::test_html_preview_cannot_reach_bridge native/test_host.py::test_native_keyboard_reaches_renderer static/tests/test_ui.py::test_keyboard_vertical static/tests/test_ui.py::test_keyboard_horizontal static/tests/test_ui.py::test_sort_options static/tests/test_ui.py::test_preview static/tests/test_ui.py::test_settings static/tests/test_ui.py::test_new_root_has_its_widening_range_immediately --native'
  ```

- **C8:**

  ```bash
  uv run --project server pytest -q server/tests/test_ui_boot.py server/tests/test_docs.py server/tests/test_review_conditions.py server/tests/test_browser_new_ui.py::test_the_keyboard_model_is_the_shared_one server/tests/test_browser_new_ui.py::test_the_markdown_preview_is_rendered_in_the_browser server/tests/test_browser_new_ui.py::test_http_entry_order_survives_name_and_metadata_sort server/tests/test_browser_new_ui.py::test_local_mode_cancels_server_search_and_restores_it server/tests/test_browser_new_ui.py::test_leaving_local_mode_restores_the_served_tree
  ```

- **C9:**

  ```bash
  uvx pre-commit run --all-files
  ```

- **C10:**

  ```bash
  uvx pre-commit run --all-files
  ```

- **C11:**

  ```bash
  node ui/core/model/test.mjs
  ```

[the 2026-10-22 architecture review]: ../reviews/2026-10-22-architecture-review.md#draft-issues
[the filemill tracker]: ../../TASKS.md
[the core initializer]: ../../ui/core/boot.js
[the static bundle]: ../../static/index.html
[the boot contract test]: ../../server/tests/test_ui_boot.py
