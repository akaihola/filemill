---
depends-on: []
---

# Document demo instances matching each browser test setup

## Original report and requirements

For user testing, document how to run on agent@gogo instances of Filemill that are
as close as possible to the browser test setup you have in the test suite. Put each
different browser test setup in its own HTTP port, and link them in
`/home/agent/index.html`. We will separately set up systemd user services for each
different browser test setup.
