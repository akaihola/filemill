Steward issue, 2026-10-22 07:16 refill (steward decisions D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Estimated 1 h.

This is draft D5 of [the 2026-10-22 architecture review](../reviews/2026-10-22-architecture-review.md#draft-issues), filed as written there; read that draft and the finding it cites before starting. The review's line numbers refer to the commit it names; recheck them on current `main`.

## Work

Add a deferred-load regression that mounts a new root while `walkPath` is waiting. Capture the originating file system and root, and check they are still current after each await and before the final state and render effects.

## Acceptance

- Releasing the old read changes no selection, path, focus or URL of the new root and issues no read through the replacement file system.
- Normal complete, truncated and declined-document walks still pass.
- The choose/refresh and preview-reuse guards stay; record in A9 that broader generation ownership remains open.

## Ground rules

- Behaviour stays the same unless the acceptance below says otherwise. Write the failing or pinning test first where the draft asks for one.
- Run at most one focused test command at a time, under your launch prompt's memory rule; no full browser suite.
- Keep private paths and host names out of committed files (the docs tests reject them).
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker](../../TASKS.md).

## Outcome, 2026-10-22

`walkPath` in [the deep-link model](../../ui/core/model/deeplink.js) captures
the root it started from. After each read it checks that root is still
mounted; if a remount replaced it, the walk returns `false` and changes no path,
selection or focus, and skips its clamped final focus too.
`applyPath` in [the deep-link module](../../ui/core/deeplink.js) reads through
the filesystem port it captured and skips its final render and scroll after a
remount. Its URL guard used to be a boolean. It now holds the root being walked:
`syncURL` is quiet only while that root is mounted, and only the walk that set
the guard clears it. Without that change, a pending stale walk held back the
new root's URL, and a stale walk ending first lifted the guard of a walk the
new root had started.

[ADR 0093](../adr/0093-a-path-walk-stops-when-its-root-is-replaced.md) records
the rule. [A9 in the architecture review](../ARCHITECTURE-REVIEW.md#a9-broader-preview-and-navigation-async-ownership)
records the resolved slice and what stays open; F5 in
[the 2026-10-22 review](../reviews/2026-10-22-architecture-review.md) points
here. The choose/refresh `navSeq` guards and the preview reuse guards are
unchanged. Same-root walks behave as before, including the URL guard: two
overlapping walks on one root still clear it when either ends.

Open, for the steward (recorded in A9, not fixed here):

- `refreshColumn` reads through the live port. After its walk is abandoned by
  a remount, it reports the first path segment as gone on the new root.
- A static-build `mount` whose walk a later mount abandoned still sets its own
  handle as `mounted`, so the remembered view of the new root can be saved
  under the old folder.
- Walks on one root still interleave with choices and with each other.

## Validation

- Red, model: the new remount case in
  [the model checks](../../ui/core/model/test.mjs) holds the walk's read with
  a controlled promise, mounts a replacement root and releases the read. On the
  old code the walk returned `true`.
- Red, browser: `test_remount_stops_pending_path_walk` in
  [the static UI tests](../../static/tests/test_ui.py) does the same through
  `applyPath` and `mount`. On the old bundle, every check failed: the walk
  returned `true`, the path became `workspace/mixed/sub`, `sel` and focus moved
  to the old chain, the URL gained `p=mixed/sub/a.py`, and `sub` was read after
  the release. With only the walk fixed, the boolean URL guard still left the
  old `p=deep` URL on the new root; scoping the guard to the root fixed it.
- Green: `node` and `deno` model checks; the two remount tests in the static
  bundle; 89 focused static bundle tests (`test_url.py`,
  `test_doc_sections.py`, `test_json_collapse.py`, `test_model.py` and the
  walk, refresh, JSONL, search, Back and preview-reuse cases of `test_ui.py`);
  64 focused server browser tests (declined documents and JSON members, Back
  and history, content search, JSON refresh, local mode, raw navigation,
  offline); 5 remount, refresh, JSONL and search tests in development mode.
- Docs: 33 documentation and review-condition tests passed with the sandbox
  off. Inside the sandbox the portability guard cannot read the masked
  `.claude/loop.md`, so that one test failed with a permission error.
- Quality gate parts: `deno fmt --check ui/`, `deno lint ui/` and
  `static/build-index.py --check` pass. No Python source changed.

## Guarded commands

Each browser and docs command ran through a wrapper that polled
`MemAvailable` and swap every two seconds, with a timeout. All started at once
with no wait; none was stopped.

| Command | Admission | Final | Start swap | Swap growth | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `pytest static/tests/test_ui.py --bundle -k remount_stops_pending_path_walk` (red) | 2,469 MiB | 2,483 MiB | 2,730 MiB | +18 MiB | 10 s | exit 1, expected |
| same, combined assertion (red) | 2,494 MiB | 2,450 MiB | 2,619 MiB | 0 MiB | 4 s | exit 1, expected |
| same, walk fixed, boolean URL guard | 2,421 MiB | 2,418 MiB | 2,600 MiB | −2 MiB | 8 s | exit 1, expected |
| `pytest static/tests/test_ui.py --bundle -k remount` (green) | 2,411 MiB | 2,414 MiB | 2,594 MiB | +2 MiB | 8 s | exit 0 |
| focused static bundle selection, 89 tests | 2,355 MiB | 2,831 MiB | 2,592 MiB | −363 MiB | 398 s | exit 0 |
| focused `server/tests/test_browser_new_ui.py` selection, 64 tests | 2,988 MiB | 3,069 MiB | 2,150 MiB | +65 MiB | 220 s | exit 0 |
| `pytest static/tests/test_ui.py --dev` selection, 5 tests | 3,078 MiB | 3,009 MiB | 2,197 MiB | −5 MiB | 37 s | exit 0 |
| `pytest server/tests/test_docs.py` (sandbox) | 3,122 MiB | 3,088 MiB | 2,187 MiB | 0 MiB | 2 s | exit 1, sandbox permission |
| `pytest` docs and review-condition tests (sandbox off) | 3,121 MiB | 3,130 MiB | 2,187 MiB | 0 MiB | 2 s | exit 0 |
