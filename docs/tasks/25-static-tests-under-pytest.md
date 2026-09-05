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
   Copy the setup code from `mount()` and `main()` in `static/test-ui.py`.
2. Create `static/tests/test_ui.py`. Move each section of `main()` into one
   `async def test_<section>(page, ...)` function. Replace each
   `check(name, cond, detail)` with `assert cond, detail`.
3. Do the same for `static/test-url.py` and `static/test-rich.py`.
4. Add a root `pytest.ini` with
   `testpaths = ["server/tests", "static/tests"]`.
5. Delete the three old scripts. Update `README.md` and CI.

## Done when

- `uv run pytest static/tests` passes in `--dev` mode and in bundle mode.
  Use a `--bundle` pytest option or an environment variable.
- `ls static/test-ui.py` reports no such file.
- A failure prints the test name, not "check failed".

## Scope

`static/tests/`, `static/test-*.py`, root pytest configuration, CI workflow.
