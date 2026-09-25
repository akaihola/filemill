---
depends-on: []
---

# Fix the extra mount prefix in rendered `~/...` Markdown links

## Original report and requirements

Bug: `[](~/...)` links are rendered incorrectly. For example, the path in
`[pykoclaw-acp/backlog/004](~/prg/pykoclaw-dev/pykoclaw-acp/backlog/004-tool-call-visibility.md#streaming-restore-plan-buffered-semantic-windows)`
is turned into the href
`/w/agent/prg/pykoclaw-dev/pykoclaw-acp/backlog/004-tool-call-visibility.md#streaming-restore-plan-buffered-semantic-windows`
when rendered. It should omit the `/w/agent/` prefix. Task
301fd540-e206-4306-b88f-5b3dbe1a15ec attempted but failed in making this link
expansion correct.

## Related work

The completed home-link expansion and [mount decision][35] predate this report.
The root-relative link fix in `a4c7707` removes the `/w/agent/` prefix and emits
`?f` for Markdown targets without an explicit view.

## Resolution (2026-09-24)

`test_home_markdown_link_is_root_relative` verifies the root-relative `~/...`
target in both rendered and source views. The issue is complete.

[35]: 35-decide-web-mounts.md
