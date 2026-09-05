---
status: unverified
---

# File-kind classification

## Review proposal

Decide each node's kind once at the filesystem seam: `folder`, `link`, `vfs`,
or `file`, with a preview hint. Producers in the Python columns/API paths and
the FSA adapter set the contract; preview, icon, and edit consumers read it.

## Evidence

Kind is re-derived by `columns.py:list_column`/`entry_icon`,
`api.py:_opens_as_folder`/`split_vfs`, `preview.py:render_preview`, and
`ui/core/render.js:NON_EDIT_RE`. The CSV provider can therefore diverge between
an empty virtual listing and a previewable file. `.jsonl` and `.desktop` link
handling must remain explicit.

## Acceptance questions

- What exact node JSON shape carries `kind` and the preview hint?
- Does the shared table cover folders, links, VFS files, ordinary files,
  `.jsonl`, and empty-provider files?
- Do server HTML, `/api/*`, FSA, icons, previews, and edit gating agree?

## Scope

`server/src/filemill/{vfs.py,columns.py,api.py,preview.py}`,
`server/src/filemill/ui/core/{render.js,jsonl.js}`, FSA/API producers, and
their focused tests.
