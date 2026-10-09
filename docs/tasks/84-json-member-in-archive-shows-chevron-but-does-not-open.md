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
