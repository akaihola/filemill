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

## Recovery findings, 2026-10-21

[The recovery task] found the report's origin and ten related test names.
It did not recover either tested revision or an eleven-test failure log.
The report cannot support a classification of all eleven failures as fixed,
still failing or obsolete. No historical browser run was attempted: choosing
the report's commit as the tested revision would be an unsupported assumption.

### Provenance and search boundary

- **Original record.** Commit `55d9267654a5ffaeb7faa195df629f2afcdb9b86`,
  dated 2026-09-05 at 02:31:48 +03:00, first adds the paragraph above to
  [the tracker]. Its subject is `chore: schedule JSON and text refresh tasks`.
  Neither its message nor its diff names the branch, either tested SHA,
  command, test nodes or log. Its parent is `3c5f88d0`; that identifies the
  preceding recorded tree, not the clean-main checkout used for the run.
- **Later copies.** `62a7402f` scheduled the same report on 2026-09-17.
  `075f6177` preserved it as active work on 2026-09-19; this is the rewritten
  identity of `d3de46c` in [the commit citation map]. `a606ae0f` extracted this
  task file that day. `24daadb6` added the evidence boundary. These changes
  add no test-run identifiers.
- **Search scope.** Searched current task and review documents, the current
  and historical [architecture review], all local Git refs for report phrases
  and relevant commit messages, and both server browser files' histories
  around September 2–20. This included retained checkpoint refs, the older
  HTML architecture review, and the later red-test record and TSV. The
  repository is not shallow. No original failure log was found in these
  sources. This is a repository evidence search, not a claim about unretained
  terminal output or session exports on other machines.
- **Other measurements.** The September 5 architecture review (`2bfe6ac1`)
  names `eae2a6d`, but reports **52 failed, 754 passed** for
  `pytest -m "not integration" --no-cov`. The browser tests carry the
  `integration` marker, so that run cannot be this browser baseline.
  [The red-test record] starts from `e142c2e4` on September 20 and records
  **256 failures** after runner repairs. Its later passing totals are not
  proof of this report's eleven-test claim. [The reviews directory] contains
  the October 21 security review, with no original browser-run inventory.
- **Review-queue state.** [The tracker reconciliation] moved this task to
  Completed / Accepted in `9d562520` using the later inventory. [The acceptance
  review] explicitly withheld acceptance because the evidence did not identify
  the original run. The earlier In Progress instruction above is historical;
  this recovery leaves the current queue placement and unchecked acceptance
  unchanged.

### Ten candidates, not an eleven-test inventory

At the report commit `55d92676`, [the keyboard browser tests] contain exactly
ten test functions that enter a legacy `/f/` URL: two URL tests and eight
mobile restore tests. The September 2 port commit `16ff8558` also explicitly
describes **eight** mobile restore tests and two URL-contract tests left on
the legacy shell. `9e931c5d` disabled its routes on September 4.

The ten names below occur in the September 20 [failure inventory]. Their
later changes are visible in `e0349caa`. These are candidate matches and
source-history dispositions, not recovered failures from this report.
Every name has the node-ID prefix
`server/tests/test_browser_keyboard.py::`.

- **Legacy URL candidate:**
  `test_legacy_query_url_canonicalizes_after_nested_navigation`.
  Removed in `e0349caa` because its route was retired.
- **Rendered-link candidate:**
  `test_rendered_relative_markdown_link_uses_root_relative_url`.
  Ported in `e0349caa` to a root-relative rendered resource URL.
- **Mobile restore candidates:** these eight were ported in `e0349caa`
  from legacy URLs/selectors to the shared UI. All eight names remain in
  the current source. Their presence is not a fresh test result.

```text
test_mobile_directory_restore_runtime_scroll_position_is_stable
test_mobile_file_restore_runtime_scroll_position_is_stable
test_mobile_file_restore_scroll_position_is_not_zero
test_mobile_restore_runtime_scroll_regression_is_covered
test_mobile_restore_preview_runtime_scroll_regression_is_covered
test_mobile_restore_regression_directory_only
test_mobile_restore_regression_preview_only
test_mobile_restore_behavior_preview_assertions
```

The acceptance review counted one legacy-query test and eight restore tests.
The rendered-link test supplies a plausible second legacy test. There is
still no ninth mobile restore name. The report could contain a counting error,
or refer to another failure or uncommitted test; the evidence cannot choose
between those explanations.

### Missing evidence

- **Revision:** the tested feature-branch SHA and clean-main SHA, plus any
  uncommitted changes. A report commit or nearby route-removal commit is not
  a substitute.
- **Failure identities:** the original eleven pytest node IDs, including any
  parameter IDs, and a log linking them to those revisions. Ten plausible
  names do not establish membership. The ninth claimed mobile case remains
  unidentified, and the claimed count remains unverified.
- **Replay context:** the original command, selection flags, browser/runtime
  versions and failure traces. Historical dependency files alone cannot show
  what the original run installed or why each test failed.

### Retirement choice for Antti

- **Choice R1 — retire the unreconstructable report.** Record an explicit
  decision to close this historical investigation without claiming that all
  eleven failures were fixed. Preserve this note and its links. Apply the
  accepted tracker state only after that decision. Keep the existing mobile
  restore and rendered-link tests and their later fixes. File any newly
  reproduced failure separately with a SHA, command and exact node ID.
- **What is lost:** a one-to-one account of the claimed eleven failures,
  verification that branch and main failed identically, and certainty that
  the unidentified case has a retained regression test. Retiring the report
  does not remove tests or prove today's suite passes.

**Recommendation:** choose R1 if the original session log cannot be supplied.
The retained history explains ten likely obsolete-route cases, but cannot
justify accepting an eleven-failure repair. This is a draft decision for
Antti; the recovery task does not apply it.

[The recovery task]: 142-recover-the-revision-and-failing-tests-of-the-old-server-browser-basel.md
[the tracker]: ../../TASKS.md
[the commit citation map]: 96-remove-the-tailnet-hostname-from-all-files-and-from-history.md#commit-citation-map
[architecture review]: ../ARCHITECTURE-REVIEW.md
[The red-test record]: ../testing/remaining-red-tests.md
[The reviews directory]: ../reviews/
[The tracker reconciliation]: 95-reconcile-tasks-md-with-the-code-16-in-progress-and-109-legacy-complet.md
[The acceptance review]: 100-check-the-19-newest-review-queue-items-against-the-acceptance-policy.md
[the keyboard browser tests]: ../../server/tests/test_browser_keyboard.py
[failure inventory]: ../testing/remaining-red-tests.tsv
