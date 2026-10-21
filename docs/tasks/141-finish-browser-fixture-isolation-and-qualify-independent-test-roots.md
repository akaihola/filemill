Steward issue, 2026-10-21 14:00 tick. Goal: agentic-leverage (filemill is tier 1 in `<steward-vault>/Goals.md`). Estimated 2 h. Source: the steward's triage of the review queue, `<steward-vault>/notes/2026-10-21-left-to-antti-triage.md`.


Two finished items wait in the review queue for the same reason: the server keyboard helper still starts its own browser lifecycle, and the application-local test roots were never qualified by a parallel whole-suite run. Triage section "Prepare the specific repairs", items "Shared Filemill browser fixtures" and "Independent Filemill test roots" (the unnumbered entries in `TASKS.md`).

## Work

1. Move the server keyboard helper onto the shared browser fixture, removing the duplicate lifecycle. Keep every existing browser assertion.
2. Run the documented parallel test command with the application roots isolated, and declare any dependency it needs.
3. Before claiming the original change is preserved or reversible, find its implementation boundary in the history and name the commits.

## Acceptance

- The documented parallel command passes with fixtures isolated, and no test starts its own browser.
- The commits of the original change and of this one are named in the task file.
- The parallel run is the heaviest command here: if hopeli can't hold it under the memory rule, record the readings and stop instead of lowering the bar. Memory: follow your launch prompt's memory rule, and run one heavy command (test suite, browser, build) at a time.


## Implementation record — 2026-10-21

The original implementation boundaries were inspected in Git:

- `b02a3ad5` (`fix(server): isolate configured test root`) replaced temporary
  mutation of the module-global default root with application-state root
  configuration and monkeypatch restoration. The application retains a default
  root for direct ASGI loading. This was not an application-factory change.
- `6390cdc0` (`test: unify browser test fixtures`) moved server fixtures into
  [the root fixtures] and introduced shared synchronous and asynchronous
  Playwright entry points. The keyboard helper still opened its own driver.
- `587752b4` (`test(static): migrate browser checks to pytest`) migrated the
  static suite and established the shared uv workspace. It retained several
  launches inside individual static tests.

These changes have separate boundaries; reverting one is not evidence that
reverting all three together is safe. No revert was performed.

### Repair and validation plan

- Add a failing source guard for browser lifecycle calls outside fixtures.
- Move the keyboard helper and direct test launches onto fixture-owned
  browsers. Keep the persistent storage profile in a dedicated fixture.
- Preserve existing assertions and application-state root restoration.
- Declare pytest-xdist in both development dependency groups and update the
  shared lock. Document root `uv run pytest -n auto` in [the contribution guide].
- Run that exact whole-suite command with memory admission, monitoring and
  process-group cleanup. A resource stop or test failure leaves acceptance open.

The lifecycle guard failed before the migration. Afterwards, it and the pytest
configuration checks passed: 11 tests in 3.07 seconds. All 783 existing assertion
ASTs in the migrated modules match after normalizing string whitespace changed
by dedenting lifecycle blocks; the keyboard module retains its 113 assertions.

The repair is commit `2d77abdd` (`test: centralize browser lifetimes and declare
parallel runner`). The task plan is `461950e5`; the canonical start move is
`66572076`. The parallel qualification run is pending.

[the root fixtures]: ../../conftest.py
[the contribution guide]: ../../CONTRIBUTING.md
