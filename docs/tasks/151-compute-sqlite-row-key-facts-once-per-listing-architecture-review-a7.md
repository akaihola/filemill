Steward issue, 2026-10-22 07:16 refill (steward decisions D53 and D95: simplification that keeps behaviour). Goal: agentic-leverage; filemill is tier 1 in `<steward-vault>/Goals.md`. Estimated 1 h.

This is draft D2 of [the 2026-10-22 architecture review](../reviews/2026-10-22-architecture-review.md#draft-issues), filed as written there; read that draft and the finding it cites before starting. The review's line numbers refer to the commit it names; recheck them on current `main`.

## Work

Add a failing query-count regression, then derive the table schema and first-column uniqueness before the row loop in `server/src/filemill/providers/sqlite.py` and format keys from the result.

## Acceptance

- One table-schema query and at most two uniqueness queries per listing, independent of row count.
- Primary-key, composite-key and fallback labels, records, order and the 500-row marker are unchanged.
- Focused provider and API checks pass. Identity encoding is unchanged and no ORM is added.

## Ground rules

- Behaviour stays the same unless the acceptance below says otherwise. Write the failing or pinning test first where the draft asks for one.
- Run at most one focused test command at a time, under your launch prompt's memory rule; no full browser suite.
- Keep private paths and host names out of committed files (the docs tests reject them).
- Handoff: a short outcome; details go in this task record.

Tracker: [the filemill tracker](../../TASKS.md).

## Outcome, 2026-10-22

`_list_rows` in
[the SQLite provider](../../server/src/filemill/providers/sqlite.py) now asks
`_key_columns` once per listing for the primary-key columns in key order and,
only for a multi-column table without a primary key, whether the first column
is unique within the first 500 rows. The module-level `_row_key` formats each
row from those facts and needs no connection. The two uniqueness counts
became one query over the same `LIMIT 500` subquery. Identity encoding,
labels and the error path are unchanged.

Semantics checked during the change:

- A listing now runs exactly one `PRAGMA table_info` query, plus at most one
  uniqueness query for a table without a primary key. It used to run one
  schema query and up to two counts per row: a 500-row table without a
  primary key ran 1,500.
- An empty table now runs the schema query once; before, it ran none. Its
  listing is still `[]`, and a failing schema query still ends in `[]`.
- The old code could probe uniqueness after a primary-key lookup failed on a
  row. That path cannot be reached: `PRAGMA table_info` and `SELECT *` name the
  same non-hidden columns, and generated columns cannot be part of a primary
  key. The new code skips the probe whenever a primary key exists. The
  per-row lookup fallbacks remain.

[A7 in the architecture review](../ARCHITECTURE-REVIEW.md#a7-sqlite-keys-collide-provider-errors-look-empty)
records the resolved slice. Lossless keys, WITHOUT ROWID tables and
distinguishable provider errors remain open there.

## Validation

- Red: `test_row_listing_reads_table_facts_once` failed in all four cases,
  primary key and unique first column at 3 and 501 rows, with 3 and 500
  schema queries per listing. Two new pinning tests passed on the old code:
  composite-key labels follow key order and spell NULL, and a NULL in the
  first column falls back to rowid labels.
- Green: all 37 tests in `server/tests/test_providers_sqlite.py`; all 86 tests
  in `server/tests/test_api.py`.
- Ruff check and format on the two changed Python files; mypy on `server/src`
  as configured in the pre-commit hook: no issues in 16 source files.
- After the final edit: the 37 provider tests and the 33 documentation and
  review-condition tests, 70 in all, passed. Inside the sandbox the docs
  portability guard could not read the masked `.claude/loop.md`, so that one
  test failed with a permission error; the same command passed with the
  sandbox off.

## Guarded commands

Each command ran through a wrapper that polled `MemAvailable` and swap every
two seconds, with a timeout. All started at once with no wait; none was
stopped.

| Command | Admission | Final | Start swap | Swap growth | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `pytest -q server/tests/test_providers_sqlite.py` (red) | 2,184 MiB | 2,329 MiB | 2,480 MiB | +38 MiB | 16 s | exit 1, expected |
| `pytest -q server/tests/test_providers_sqlite.py` (green) | 2,444 MiB | 2,323 MiB | 2,525 MiB | +16 MiB | 14 s | exit 0 |
| `pytest -q --durations=5` provider and SQLite API selection | 2,453 MiB | 2,351 MiB | 2,539 MiB | +27 MiB | 15 s | exit 0 |
| `pytest -q server/tests/test_api.py` | 2,336 MiB | 2,470 MiB | 2,566 MiB | −32 MiB | 12 s | exit 0 |
| `mypy … server/src` (pre-commit hook form) | 2,518 MiB | 2,773 MiB | 2,665 MiB | +23 MiB | 21 s | exit 0 |
| `pytest -q` provider, docs and review-condition tests (sandbox) | 2,646 MiB | 2,709 MiB | 2,677 MiB | +2 MiB | 6 s | exit 1, sandbox permission |
| `pytest -q` provider, docs and review-condition tests (sandbox off) | 2,689 MiB | 2,740 MiB | 2,676 MiB | +49 MiB | 22 s | exit 0 |
