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

The completed home-link expansion and [mount decision][35] are earlier work.
This report specifically rejects the resulting `/w/agent/` prefix and remains
open independently of those completed tasks.

[35]: 35-decide-web-mounts.md
