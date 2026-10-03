---
depends-on: []
---

# Fix server test fixture discovery

## Original report and requirements

Does the documented way to run server tests still silently lose every fixture:
does `server/pyproject.toml` still win the rootdir election, so the conftest that
moved to the repo root is never loaded and we get a wall of "fixture not found"?
Should we use `server/.venv/bin/pytest -c pytest.ini server/tests/...` from the root
until that is fixed?
