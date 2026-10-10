---
depends-on: []
---

# JSON member in an archive shows a chevron but does not open

## Original report and requirements

A session in `~/prg/filemill-screencast` found this on 2026-10-09 at HEAD
`7ff1fd2`, in the server edition.

Put `data.json` inside `bundle.zip`. Open `bundle.zip`. The row for `data.json`
shows the "›" chevron, which says that the entry opens as a column. It does not
open. Its preview is highlighted source, not the foldable JSON view.

The same file on disk opens as columns of its keys and previews as foldable
JSON. `member_preview_response` (`server/src/filemill/api.py:315`) says a member
renders "the way the same file would render on disk".

## Acceptance

- A `.json` member opens as columns of its keys and previews like the same file
  on disk. Check `.jsonl` members too.
- If that cannot be done, the member shows no chevron.

## Cause and fix (2026-10-11)

The JSON wrapper (`ui/adapters/vfs-json.js`) marks a `.json` member as a
column, which is the chevron, and then reads the file with its virtual path
cleared. `HTTP.blob` (`ui/adapters/http.js`) never sent a virtual path at all,
so the read fetched the archive's own bytes, `JSON.parse` failed and the node
quietly turned back into a leaf whose preview came from the server as
highlighted source. A `.jsonl` member kept its virtual path but failed the same
way in `HTTP.blob`.

`HTTP.blob` now sends `v` when the node has a virtual path, and the JSON
wrapper keeps the node's virtual path when it reads. `/api/raw?p=…&v=…`
already served member bytes. [ADR 0072] records the behaviour.

## Validation

- `server/tests/test_browser_new_ui.py`: a `.json` member opens as columns of
  its keys and previews as foldable JSON, a deep link into a JSON member
  reloads, and a `.jsonl` member opens as a column of rows. Red before the
  fix, green after.
- `static/index.html` rebuilt with `static/build-index.py`.

[ADR 0072]: ../adr/0072-archives-browse-by-their-members.md
