---
status: unverified
---

# VFS ViewSpec

## Review proposal

If a fourth provider or a pagination bug creates real pressure, bundle view
mechanics in `ViewSpec(fmt, page, limit)` and change providers to accept
`(path, vpath, view)`. Preserve any still-required column selection behavior.

## Evidence

`VFSProvider.render_preview(path, vpath, fmt, page, limit, col)` exposes six
parameters, and callers include `api.py:vfs_preview`, `app.py:click`,
`vpage`, `_representation_html`, and `columns.py:list_vfs_column`. The review explicitly
marks this speculative and conditional.

## Acceptance criteria

- Do not implement without the stated trigger.
- If triggered, all providers and callers use the value object and existing
  format, pagination, and column behavior remain covered.

## Scope

`server/src/filemill/{vfs.py,api.py,app.py,columns.py}`, provider modules, and
VFS route/protocol tests.
