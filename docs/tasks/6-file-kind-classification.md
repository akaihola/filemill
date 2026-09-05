---
status: unverified
---

# Decide the file kind once

## Proposal

When Filemill reads a file system entry, it should decide its kind one time.
The kind must be one of `folder`, `link`, `vfs`, or `file`. The entry should
also say how the UI can preview it.

The code that reads entries, including the Python API and the File System
Access adapter, should set these values. Code that shows an icon, opens a
preview, or enables editing should use these values.

## Evidence

Several parts of the code decide the kind again. These include
`columns.py:list_column` and `entry_icon`, `api.py:_opens_as_folder` and
`split_vfs`, `preview.py:render_preview`, and
`ui/core/render.js:NON_EDIT_RE`.

These decisions can disagree. For example, the CSV provider can return no
virtual entries. One code path then treats the CSV file as an empty folder,
while another treats it as a file that can be previewed. Keep `.jsonl` and
`.desktop` handling in the new design.

## Questions to answer

- What exact fields carry the kind and preview information?
- Does the rule cover folders, links, VFS files, normal files, `.jsonl`, and
  files whose provider returns no entries?
- Do the server HTML, `/api/*`, File System Access, icons, previews, and edit
  controls all give the same result?

## Scope

`server/src/filemill/{vfs.py,columns.py,api.py,preview.py}`,
`server/src/filemill/ui/core/{render.js,jsonl.js}`, FSA/API producers, and
their focused tests.
