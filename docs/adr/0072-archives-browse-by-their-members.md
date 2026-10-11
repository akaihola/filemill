# ADR 0072: Archives browse by their members

Date: 2026-10-07.

## Context

A `.tar.zst` backup holds files the user wants to look at: a manifest, a
configuration, a log. Opening it meant extracting it somewhere first. A SQLite
database already opens as a column of tables ([ADR 0070] lists the other file
kinds that open as columns), through a provider registered in `vfs.py`.

Only the server can read inside a compressed archive: the browser has no zstd
decoder, and a tar stream must be decompressed to list it at all.

## Decision

A tar archive — plain, gzip, bzip2, xz or zstd — and a zip open as a column of
their members in the server edition. The provider is
`providers/archive.py`. A member path `docs/readme.md` is the row `readme.md`
in the column `docs`; directories a tar never recorded are implied by the
members below them. Members whose names escape (`..`) are dropped from the
listing; nothing is ever extracted to disk.

A file member previews as the file it is. The client sends the member's
virtual path with the preview request (`/api/preview?p=…&v=…`); the server
reads the member's bytes, writes them to a temporary file under the member's
own name so that the suffix picks the renderer, and renders it through the same
`render_preview` as a file on disk. An image or a PDF member fetches itself
from `/api/raw?p=…&v=…`, which serves the member's bytes with a media type
guessed from its name.

A JSON or JSONL member is browsed in the browser, as the same file on disk is
(`ui/adapters/vfs-json.js`): the browser reads the member's bytes from
`/api/raw?p=…&v=…` through `FS.blob`, which sends the node's virtual path, and
opens the member as columns of its keys or rows with the foldable JSON preview.
Until 2026-10-11 the read dropped the virtual path and fetched the archive
itself, so the member showed a chevron that opened nothing ([84]).

Review follow-up, 2026-10-11: a JSON or JSONL member that cannot be browsed
becomes a leaf and loses its chevron. Cached rows update the indicator without
rebuilding the parent column. If the read outlasts the navigation grace period,
the navigator closes the loading column and keeps the member selected. JSON
size failures and JSONL read/parse failures show an error in the preview;
invalid JSON keeps the existing source fallback. Rewalking a cached path keeps
declined entries as leaves until a refresh replaces the listing.

The same holds for every kind the browser renders from bytes on disk —
Markdown, `.docx` and `.pptx` (`ui/adapters/app-http.js`): the server's
virtual-leaf wrapper leaves those members to the browser's rich renderer,
which reads them through `FS.blob`. A Markdown member also opens as columns
of its headings (`ui/adapters/vfs-doc.js`), the way the same file on disk
does. A reStructuredText member stays a plain file: its sections render on
the server, which has no route for a member plus a line span. Under
`?filemill=highlight` a member still asks the server, whose answer is the
member's coloured source. Until 2026-10-11 every member asked the server,
so a Markdown member previewed as coloured source ([86]).

The work is bounded. The member index stops at `MAX_MEMBERS` entries and is
cached per path, size and mtime, so one directory listing that asks "is this
archive non-empty?" costs one walk, not one per request. A member over
`MEMBER_MAX` is listed and named but not read; its preview says so and the raw
route answers 413.

Zstandard comes from the standard library on Python 3.14 and from the
`zstandard` package before that; `pyproject.toml` pins the package for older
interpreters only. The static edition does not open archives.

## Consequences

`vfs.py` gains a second protocol, `VFSMemberProvider`, for providers whose
leaves have bytes: archives have them, database rows do not. The server
edition's preview chain gains one wrapper that sends a server-listed virtual
leaf to the server instead of to the local renderer, which would have fetched
the whole archive. A zip is listed from its central directory; a tar is walked
once per listing and once more per member read, so a large compressed tar is
slow to open and slow to preview from, in proportion to its size.

[84]: ../tasks/84-json-member-in-archive-shows-chevron-but-does-not-open.md
[86]: ../tasks/86-markdown-in-archives-is-not-rendered.md
