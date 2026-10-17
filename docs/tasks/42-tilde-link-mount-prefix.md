---
depends-on: []
---

# Fix the extra mount prefix in rendered `~/...` Markdown links

## Original report and requirements

Bug: `[](~/...)` links are rendered incorrectly. For example, the path in
`[project/notes/topic](~/projects/example/notes/topic.md#section)`
is turned into the href
`/w/<root-name>/projects/example/notes/topic.md#section`
when rendered. It should omit the `/w/<root-name>/` prefix. Task
301fd540-e206-4306-b88f-5b3dbe1a15ec attempted but failed in making this link
expansion correct.

## Additional original report and requirements

Task 645b5e03-8b7c-4a29-b56c-0d96f9add7cd tried to fix `[](~/...)` links, and it
kind of did, but they now point to the deprecated `/w/home/<user>/...` paths. Fix them
to point to `/...?f` relative to the root mount directory instead. Example:
[`project/notes/topic`](~/projects/example/notes/topic.md#section)
currently points to
`/w/<root-name>/projects/example/notes/topic.md?filemill=render#section`
but it needs to point to
`/projects/example/notes/topic.md?f#section`
instead.

## Related work

The completed home-link expansion and [mount decision][35] predate this report.
The root-relative link fix in `a4c7707` removes the `/w/<root-name>/` prefix and emits
`?f` for Markdown targets without an explicit view.

## Resolution (2026-09-24)

`test_home_markdown_link_is_root_relative` verifies the root-relative `~/...`
target in both rendered and source views. The issue is complete.

[35]: 35-decide-web-mounts.md
