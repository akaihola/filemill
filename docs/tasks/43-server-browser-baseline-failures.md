---
depends-on: []
---

# Investigate the 11 server browser failures also reproduced on main

## Original report and requirements

The server browser suites show 11 failures on the branch, but a run against a clean
main checkout produced exactly the same 11: two legacy-htmx tests that main
deliberately disabled, and nine mobile restore-scroll tests.

## Evidence boundary

The count above is the original report, not a fresh test result. It does not
identify the branch revision or list the nine mobile test names. Preserve its
In Progress placement from tracker audit `d3de46c`; do not infer completion
from another task's baseline comparison.
