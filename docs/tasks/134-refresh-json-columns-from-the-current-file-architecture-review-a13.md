Steward issue, 2026-10-20 22:30. Goal: agentic-leverage (filemill is tier 1). Estimated 0.5 h.

Draft A13 of [the re-checked architecture review](../ARCHITECTURE-REVIEW.md#a13-json-column-refresh-keeps-the-old-parsed-value) (filemill [132], 2026-10-20): the JSON column's refresh rebuilds from a value parsed earlier, so an edit made outside Filemill stays invisible while the UI reports no change.

## Work

Give the virtual JSON adapter ownership of invalidation: on refresh, read the backing file or archive member again before rebuilding the column's children. Don't teach the core every parser's fields. Coordinate with the navigation and preview invalidation described under A9, without implementing A9.

## Acceptance

- Failing regressions first, for an open JSON column after an external edit, a removed key, a parse failure and a changed archive member.
- The column's own refresh reads the source again, updates the preview and the selection, and reports a parse error instead of keeping stale values.
- Static and development modes and served mode agree.
- The relevant port decision and documentation describe the new behaviour; the review's A13 entry says it is resolved.
- The suites you touched pass, under the same memory rule as filemill's other steward issues: wait up to 10 minutes for 2 GiB `MemAvailable`, start at 1.5 GiB or more, stop below 1 GiB or on 512 MiB of swap growth, one suite at a time.

## Implementation plan

- Add browser regressions for edits, removed keys and invalid input. Exercise
  the root JSON column and a nested column in both static builds. Test a real
  file and a ZIP member in served mode.
- Add an optional FS invalidation hook. The JSON adapter clears its parsed
  source and byte metadata, then resolves a nested column from the new source.
- Keep the existing navigation sequence, selection walk and preview rendering.
  Do not implement the broader A9 ownership changes.
- Update the port decision and A13. Run each affected suite separately with
  the required memory guard, then merge and complete the canonical tracker.

## Implementation, 2026-10-21

The FS port has an optional `invalidate(node)` hook. The JSON adapter owns
parsed-source invalidation. The backing file adapter clears cached file bytes
and metadata. A nested column reads its source root again and resolves its
structural path from the new value. Core retains its existing navigation
sequence and selection walk. Parse errors use the common `denied` field and
appear beside the current source in the preview.

[The port decision] and [the refresh decision] describe the contract.
[A13] is resolved. A9's wider navigation and preview ownership work remains
outside this repair.

Before the fix, all six static regressions failed for root and nested edits,
removed keys and parse failures. The served regressions also reproduced stale
values for real files and changed ZIP members.

## Validation, 2026-10-21

- JSON tests: 17 passed in bundle mode and 17 in development mode.
- Final stronger JSON regressions plus the existing folder-refresh test:
  7 passed in each static mode.
- Final served refresh checks: 19 passed. These include all 12 combinations
  of real file or ZIP member, root or nested column, and edit, removed key
  or parse failure.
- The broader served UI, documentation and browser-wait run finished with
  293 passes and 3 failures. Two failures exposed missing HTTP metadata after
  invalidation. The HTTP port now preserves unknown metadata as a valid state;
  all affected cases pass in the final 19-check run.
- The remaining failure was the existing Back/Forward history test. It also
  failed in the first focused run. It passed alone on both the unchanged
  starting source and the final implementation. No history code or assertions
  changed. The intermittent failure remains part of the validation record.
- Model checks, Ruff, Deno formatting and lint, mypy, and bundle consistency
  passed. All seven pre-commit hooks passed. The first gate flagged a
  concurrent validation-note edit; the rerun passed with the tree unchanged.

Final focused commands:

```bash
uv run --project server pytest -q static/tests/test_json_collapse.py static/tests/test_ui.py -k 'current_file or refresh' --bundle
uv run --project server pytest -q static/tests/test_json_collapse.py static/tests/test_ui.py -k 'current_file or refresh' --dev
uv run --project server pytest -q server/tests/test_browser_new_ui.py -k refresh
uvx pre-commit run --all-files
```

Each test run used the requested memory guard, with one suite at a time.
Starts had at least 2 GiB available; no run hit the 1 GiB stop threshold or
512 MiB swap-growth limit. Final bundle/development refresh runs had minimum
available memory of 2584/2706 MiB and no swap growth. The final served refresh
run had at least 2446 MiB available and 2 MiB maximum swap growth.

No remote push or deployment was performed. Shared main contained 75
unpublished commits before the implementation merge.

[The port decision]: ../adr/0041-core-adapters-three-ports.md#refresh-invalidation-2026-10-21
[the refresh decision]: ../adr/0051-refresh-empties-node-kids-and-re-enters-ensureloaded.md#adapter-caches-2026-10-21
[A13]: ../ARCHITECTURE-REVIEW.md#a13-json-column-refresh-keeps-the-old-parsed-value
