---
depends-on: []
---

# Scope CI cancellation to the same branch or pull request

## Problem

`.github/workflows/publish.yml` uses workflow-wide `group: pages` with
`cancel-in-progress: true`. Every main push, pull request and manual run shares
that group, so an unrelated PR can cancel a main run or another PR's tests.
This risks wasting completed work and delaying publication.

## Requirements

Use `${{ github.workflow }}-${{ github.ref }}` as the workflow concurrency
group, retaining `cancel-in-progress: true`. New runs supersede obsolete runs
for the same ref, while distinct PR refs and main run independently. Preserve
main-only publication and its dependency on every quality check. Keep Pages
deployments serialized; if a separate deployment concurrency group is needed,
apply it only to the publishing job.

The expression follows
[GitHub's workflow concurrency guidance](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).

## Acceptance

- First add a failing regression check for the shared group, then verify that
  concurrency includes both the workflow and ref and still cancels superseded
  runs for the same ref.
- Verify that two PR refs, and main versus a PR ref, produce different groups;
  repeated runs of the same workflow/ref produce the same group.
- PRs cannot cancel main through the concurrency group or publish to Pages.
  Main publishing still requires all checks to pass.

## Implementation (2026-10-14)

The workflow-level group is now `${{ github.workflow }}-${{ github.ref }}`
with `cancel-in-progress: true`. No separate deployment group was added: only
main publishes, and all main runs share one group, so Pages deployments stay
serialized. A job-level group could not protect a deployment anyway, because
workflow-level cancellation cancels the whole run.

`server/tests/test_pytest_config.py` covers it:

- `test_ci_cancels_only_superseded_runs_of_the_same_ref` failed against
  `group: pages` and passes now. It substitutes `github.workflow` and
  `github.ref` into the group and checks that repeated main or PR runs share a
  group, while two PR refs, main versus a PR, and two workflows differ.
- `test_ci_publishes_only_from_main_after_every_check` guards that `publish`
  needs `test` (which needs `lint`) and runs only for main outside pull
  requests.
