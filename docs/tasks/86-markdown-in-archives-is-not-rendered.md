---
depends-on: []
---

# Markdown in archives is not rendered

## Original report and requirements

A session in `~/prg/filemill-screencast` found this on 2026-10-09 at HEAD
`7ff1fd2`, in the server edition.

A Markdown file on disk shows rendered. A Markdown member of an archive shows
as highlighted source.

The browser renders Markdown and `.docx` from the modules in `ui/vendor/`
(`ui/adapters/app-http.js:73-83`). An archive member preview comes from the
server instead: `member_preview_response` (`server/src/filemill/api.py:315`)
calls `render_preview`, which does not dispatch Markdown or `.docx`
(`server/src/filemill/preview.py:57-62`). `member_preview_response` says a
member renders "the way the same file would render on disk".

## Acceptance

- A Markdown member previews rendered, like the same file on disk.
- A `.docx` member previews rendered, like the same file on disk.
- Decide if a Markdown member also opens as columns of its headings, like on
  disk. Record the decision.

## Cause and fix (2026-10-11)

The server edition's preview chain (`ui/adapters/app-http.js`) sent every
server-listed virtual leaf to `/api/preview`, and `render_preview` has no
Markdown or `.docx` renderer, so a member fell through to coloured source.
Since [84], `HTTP.blob` fetches a member's bytes with its virtual path, so
the browser's rich renderer can read a member exactly as it reads a file on
disk. The virtual-leaf wrapper now leaves Markdown, `.docx` and `.pptx`
members to `PreviewRich`; `?filemill=highlight` still asks the server, whose
answer for a member is its coloured source, as for a file on disk.

One more thing stood in the way: `classifyFile(name, node)` answers
"virtual" for any node with a virtual path, which says where the bytes live
rather than what they are, so both the chain and `PreviewRich` saw a
database row where a `.md` file was. `fileKind` (`ui/core/file-kind.js`)
classifies the file a node names with its virtual path left out, and both
use it.

## Decision: a Markdown member opens as columns of its headings

Yes. [84] made a JSON member open as columns of its keys "like the same
file on disk", and the document wrapper (`ui/adapters/vfs-doc.js`) reads
the member through the same `FS.blob`, so the outline, the section
previews and the deep links work unchanged. A reStructuredText member stays
a plain file: its sections render on the server from a line span, and
`/api/preview` has no member-plus-lines route. [ADR 0072] records both.

## Validation

- `server/tests/test_browser_new_ui.py`: a Markdown member renders in the
  browser, opens as columns of its headings and a section deep-links; a
  `.docx` member renders. Red before the fix, green after.
- `static/index.html` rebuilt with `static/build-index.py`.

[84]: 84-json-member-in-archive-shows-chevron-but-does-not-open.md
[ADR 0072]: ../adr/0072-archives-browse-by-their-members.md
