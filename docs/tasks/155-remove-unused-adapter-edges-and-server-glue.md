Steward issue, 2026-10-22 08:54 refill (steward decisions D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Estimated 45 min.

This is draft D6 of [the 2026-10-22 architecture review](../reviews/2026-10-22-architecture-review.md#draft-issues), filed as written there; read that draft and finding F6 before starting. The review's line numbers refer to the commit it names; recheck them on current `main`, since [150] has since retired the Python WebVTT renderer.

## Work

Recheck callers, then remove the three dead imports, `_HTML_EXTS`, the unused integer conversion and the internal `is_vfs_file` helper. Retire tests that only assert the removed wrapper; keep the registry behaviour checks. Update the review's A12 remaining list; Source routing decisions stay with A8.

## Acceptance

- Development and bundled module graphs still load.
- Current string, default and path query dispatch and provider lookup tests pass.
- No replacement abstraction and no behaviour change.
- No service restart is needed; don't restart `filemill` or `filemill-public`.

## Ground rules

- Run at most one focused test command at a time, under your launch prompt's memory rule; no full browser suite.
- Keep private paths and host names out of committed docs and code (the docs tests reject them). The check receipt (`*.evidence.json`) is exempt.
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker](../../TASKS.md).

[150]: 150-retire-the-unreachable-python-webvtt-renderer-architecture-review-a12.md

## Plan

Recheck each edge on current `main` before deleting it:

1. Drop the unused `render` imports from `ui/adapters/vfs-json.js` and
   `ui/adapters/vfs-csv.js`, and the unused state `path` import from
   `ui/adapters/router-path.js`. The `render` and `path` names left in those
   files are method names, a property key and a parameter, not the imports.
2. Drop `_HTML_EXTS` and the `int` query conversion from
   `server/src/filemill/app.py`. No registered endpoint annotates a
   parameter as `int`, so every query value already reached its handler as a
   string.
3. Drop `is_vfs_file` from `server/src/filemill/vfs.py`; only two tests
   called it. Keep what those tests checked about the shipped registry (a
   `.db` file has the SQLite provider, a `.txt` file has none) by asking
   `REGISTRY.get` directly.
4. Rebuild the bundle, compare module evaluation order per entry, and update
   A12 in [the architecture review](../ARCHITECTURE-REVIEW.md#a12-smaller-defects-dead-code-and-audits).
   Leave `render_source`, the unused `state` argument and Source routing to A8.

## Outcome, 2026-10-22

Removed the three unused imports, `_HTML_EXTS`, the `int` query conversion
(its loop now iterates over parameter names only) and `is_vfs_file`. The two
`is_vfs_file` tests became `test_registry_has_a_provider_for_db` and
`test_registry_has_no_provider_for_txt`, which ask `REGISTRY.get` the same
questions about the shipped registry. A12 in the architecture review now lists
what remains: the unused `state` argument and test-only `render_source` in
`preview.py` (A8 owns the Source decision), five hand-built preview-error
sites, and comments that restate code.

No behaviour changed and no replacement abstraction was added. The committed
`static/index.html` is byte-identical after `static/build-index.py`, because
the bundler strips import lines. Module evaluation order is unchanged for
`entry-static.js`, `entry-server.js` and `entry-native.js`: `core/render.js`
and `core/model/state.js` already evaluate before these adapters through
other imports. No service restart was needed or made.

Not done, as out of scope: the repository's Deno config disables
`no-unused-vars`, and a run with only that rule reports many more unused
bindings across `ui/`. Enabling the rule or clearing those is separate work.

### Checks

- Red: `deno lint --no-config --rules-tags= --rules-include=no-unused-vars`
  on the three adapters reported exactly the three imports; after the change
  it reports none. `vulture` reported `is_vfs_file` as unused; `git grep`
  found no reader of `_HTML_EXTS` and no `int`-annotated route parameter.
- `deno fmt --check ui/`, `deno lint ui/`, `ruff check server`,
  `ruff format --check server/src server/tests` and the gate's `mypy`
  command: clean.
- `static/build-index.py` then `static/build-index.py --check`: up to date,
  no diff in `static/index.html`.
- Focused server suites (`test_vfs`, `test_routes_new`, `test_resource_routes`,
  `test_app`, `test_api`, `test_urls`, the four provider suites,
  `test_public_mode`, `test_resource_safety`, `test_save_safety`,
  `test_mutation_policy`, `test_host_policy`): 726 passed. These cover string,
  default and path dispatch through `rt` and provider lookup.
- Development graph: `pytest static/tests/test_ui.py --dev -k jsonl_rows`,
  1 passed. Bundled graph: the same with `--bundle`, 1 passed.
- Server edition graph (`router-path.js`, `vfs-json.js`, `vfs-csv.js`):
  `test_no_console_errors`, `test_the_url_path_mirrors_the_file_path`,
  `test_stepping_over_sibling_folders_rewrites_history`,
  `test_a_jsonl_file_opens_as_a_column_of_rows` and
  `test_a_csv_row_previews_headers_and_quoted_values` in
  `server/tests/test_browser_new_ui.py`, 5 passed.
- Docs guards: `server/tests/test_docs.py` and
  `server/tests/test_review_conditions.py`, 33 passed.

### Guarded heavy commands

Each ran alone under a guard that would stop it below 1024 MiB available or
on 512 MiB of swap growth. MemAvailable and swap are in MiB.

| Command | Outcome | Admission | Final | Start swap | Swap growth | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Focused server suites above | started at once, no wait | 2862 | 2825 | 2272 | 30 | 60 s | exit 0 |
| Static `--dev` JSONL test | started at once, no wait | 2931 | 2755 | 2320 | 3 | 25 s | exit 0 |
| Static `--bundle` JSONL test | started at once, no wait | 2837 | 2748 | 2308 | 1 | 27 s | exit 0 |
| Server-edition browser tests | started at once, no wait | 2847 | 2802 | 2306 | 0 | 34 s | exit 0 |
