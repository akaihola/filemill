---
status: closed
---

# Group VFS preview settings

## Proposal

Closed by [34]: the six-argument `render_preview` interface no longer exists.

Do this only if a fourth provider or a pagination bug shows that the current
interface causes real problems. Put the preview settings in a
`ViewSpec(fmt, page, limit)` object. Change providers to accept
`(path, vpath, view)` instead of six separate arguments. Keep column selection
if the code still needs it.

## Evidence

`VFSProvider.render_preview(path, vpath, fmt, page, limit, col)` has six
arguments. Callers include `api.py:vfs_preview`, `app.py:click`, `vpage`,
`_representation_html`, and `columns.py:list_vfs_column`. The review marks this
idea as speculative. Do not start it without the stated trigger.

## Acceptance criteria

- Do not implement this proposal without the stated trigger.
- If the trigger occurs, all providers and callers use `ViewSpec`.
- Tests continue to cover format selection, pagination, and column selection.

## Scope

`server/src/filemill/{vfs.py,api.py,app.py,columns.py}`, provider modules, and
VFS route/protocol tests.
