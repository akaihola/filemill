# Testing documentation

Use the [contributor guide] for current suite and gate commands, the [server
test guide] for browser prerequisites, and the [native guide] for native checks.
Root pytest collects the server and static bundle tests. Static development,
native and the interactive picker require their own runs.

## Documentation changes

From the repository root:

```bash
timeout 600 uv run --project server pytest -q server/tests/test_docs.py server/tests/test_review_conditions.py
```

These are the tests that read repository Markdown at this review's baseline.
Search again when adding or moving documentation tests. [Documentation checks]
cover portability, selected claims and a documented server command.
[Review-condition checks] also read the rich-consent ADR. Tests that read
temporary Markdown fixtures test application behavior, not repository prose.
A documentation-only change does not need browser suites.

Focused regression entry points include [static JSON refresh], [served UI]
and [static UI]. Run affected static tests in both bundle and development
modes when shared behavior changes. The [waiting policy] explains readiness
and controlled response delays.

## Historical evidence

The [remaining-red-tests record] and its [failure inventory] describe the
September 2026 baseline. The TSV holds 256 historical failed node IDs plus
its header. Many names and commands have since changed. Keep it as evidence;
do not use it as a current skip list, failure count or runnable suite list.
Its dated corrections remain intact. The [architecture review] records later
repairs; the [documentation review] records this audit.

[contributor guide]: ../../CONTRIBUTING.md#tests
[server test guide]: ../../server/CONTRIBUTING.md#running-tests
[native guide]: ../../native/README.md#checks
[Documentation checks]: ../../server/tests/test_docs.py
[Review-condition checks]: ../../server/tests/test_review_conditions.py
[static JSON refresh]: ../../static/tests/test_json_collapse.py
[served UI]: ../../server/tests/test_browser_new_ui.py
[static UI]: ../../static/tests/test_ui.py
[waiting policy]: ../../server/CONTRIBUTING.md#wait-for-an-element-never-for-a-duration
[remaining-red-tests record]: remaining-red-tests.md
[failure inventory]: remaining-red-tests.tsv
[architecture review]: ../ARCHITECTURE-REVIEW.md
[documentation review]: ../reviews/2026-10-22-docs-review.md
