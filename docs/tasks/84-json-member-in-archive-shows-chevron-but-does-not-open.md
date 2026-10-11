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

## Independent review follow-up, 2026-10-11

R1 found an unmet fallback requirement. A JSON member above 8 MiB becomes a
leaf but its cached row keeps the chevron. A JSONL member above the server's
16 MiB member limit keeps directory status and opens an empty error column.
These paths predate the member-byte fix.

Rejected JSONL files now become leaves with their read/parse error in the
preview. Rendering removes stale chevrons without rebuilding the parent
column. The navigator closes a declined loading column, preserving the member
selection. Rewalking a cached path leaves declined entries as leaves until a
refresh replaces the listing. Invalid JSON retains its source fallback.

Validation:

- Four oversized-member cases, JSON above 8 MiB and JSONL above 16 MiB, with
  ordinary and deferred reads: all failed on retained chevrons before the fix
  and passed afterward. They also check column removal, parent row identity,
  visible errors, reselection, cached path restoration, and reloads.
- 24 focused browser tests passed for JSON, JSONL, archives, and Git bundles.
- The static UI suite passed against both the generated bundle and `--dev`,
  including invalid JSON/JSONL fallback checks.
- 553 non-browser server tests passed. Model checks, Deno formatting/lint,
  Ruff, mypy, bundle freshness, and `git diff --check` passed.
- The shared static bundle, architecture record, and ADRs 0029/0072 are updated.

User acceptance remains pending.
