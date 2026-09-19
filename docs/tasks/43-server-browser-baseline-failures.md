---
depends-on: []
---

# Investigate the 11 server browser failures also reproduced on main

## Original report and requirements

The server browser suites show 11 failures on the branch, but a run against a clean
main checkout produced exactly the same 11: two legacy-htmx tests that main
deliberately disabled, and nine mobile restore-scroll tests.
