---
depends-on: [12]
---

# Move the static test scripts under pytest

## Goal

`uv run pytest` at the repository root runs the static browser checks. Each
check is one test function. Roadmap phase 7, step 1.

## Steps

1. Create `static/tests/conftest.py`. Add fixtures for: the fake directory
   handle, the OPFS root, and a local HTTP server that serves the bundle.
   Copy the setup code from `mount()` and `main()` in `static/tests/test_ui.py`.
2. Create `static/tests/test_ui.py`. Move each section of `main()` into one
   `async def test_<section>(page, ...)` function. Replace each
   `check(name, cond, detail)` with `assert cond, detail`.
3. Do the same for `static/tests/test_url.py` and `static/test-rich.py`.
4. Add a root `pytest.ini` with
   `testpaths = ["server/tests", "static/tests"]`.
5. Delete the three old scripts. Update `README.md` and CI.

## Done when

- `uv run pytest static/tests` passes in `--dev` mode and in bundle mode.
  Use a `--bundle` pytest option or an environment variable.
- `ls static/tests/test_ui.py` reports no such file.
- A failure prints the test name, not "check failed".

## Scope

`static/tests/`, `static/test-*.py`, root pytest configuration, CI workflow.

## Implementation plan

- Preserve the existing browser assertions and performance budgets. Give each
  former `main()` section a fresh page and its own test name.
- Put fake-handle setup, the loopback server with rich-renderer stubs, bundle
  selection and OPFS lifecycle in `static/tests/conftest.py`.
- Move the five existing static pytest modules into the same directory. Keep
  the real-picker script manual. Remove the old aggregate entry points and
  result counters.
- Add a root uv workspace and move the existing lock to the root. Keep the
  server's dependency versions and Playwright pin. Add `pytest-asyncio` for
  async tests and fixtures.
- Update CI, current test instructions and the RST measurement script that
  used the retired rich-test HTTP server.
- Validate collection from the root, static tests in bundle and development
  modes, server tests, pre-commit and the generated bundle check.

## Validation and merge blocker, 2026-10-17

- Root collection finds 993 tests: 846 server tests and 147 static tests.
- `uv run pytest static/tests --dev -xq --tb=short`: 147 passed.
- `uv run pytest static/tests --bundle -xq --tb=short`: 147 passed.
- The isolated folding section now focuses the leaf preview and waits for
  scrolling to settle. The old `main()` inherited that state from the keyboard
  checks. Its updated setup passes in both modes.
- Static Ruff checks and formatting pass. All six pre-commit hooks pass with
  Python 3.13. The bundle freshness check passes.
- The shared lock preserves all existing dependency versions. Only
  `pytest-asyncio` is added.
- `uv run pytest server/tests -q --tb=short`: 844 passed, two failed.
  Both failures reproduce in a detached checkout of starting commit
  `7c0f8ee4`, with the original dependency lock:
  - `test_a_git_bundle_opens_as_refs_then_files_and_a_file_previews` times out
    waiting for the first bundle column.
  - `test_delete_key_deletes_selected_files_and_directories_but_not_editors`
    records a 404 console error.
- The 15 Git-bundle provider tests pass. Configuration and live-document
  checks pass, 22 tests in total.

The server failures are outside this migration's scope. The roadmap's red-suite
rule blocks merging this branch. Keep task 25 In Progress until that gate is
resolved; user acceptance remains unchecked.

## Superseding completion, 2026-10-17

[99] rebased this migration onto current main and merged it as `adb7aef3`.
The root suite passed all 1,000 tests in 815.02 s. The full server suite and
both static modes then passed twice consecutively on main: 853 server tests
and 147 tests in each static mode per run. All six pre-commit hooks pass with
Python 3.14. The fixed-wait search is empty.

See [99's validation](99-rebase-25-s-pytest-migration-onto-main-and-merge-it-once-the-full-suit.md) for the six
main timings and the regression fixes. These results supersede the merge
blocker above. The original worktree and branch remain at `b8e8c588`.
Completed pending user acceptance.
