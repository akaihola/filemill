# ADR 0070: Markdown and reStructuredText browse by their headings

Date: 2026-10-07.

## Context

A JSON, JSONL, CSV or SQLite file opens as a column: its keys, rows or tables
are rows the user can step through, and a row previews on its own. A long
Markdown or reStructuredText file had no such view. The preview pane showed the
whole file, and finding one section meant scrolling it.

The outline of a document is in its headings. Markdown has ATX and setext
headings; reStructuredText has titles with underline or overline adornments
whose nesting follows the order the styles first appear in.

## Decision

A `.md`, `.markdown` or `.rst` file is a document. In a folder column it is
a row like any file, with its own icon and a `›`. Opening it shows a column of
its top-level sections; a section with subsections opens as another column.
A section previews as its own lines, rendered by the same renderer as the whole
file, and a `?filemill=highlight` view shows those lines as source.

The document stays a file. Selected in its folder, or opened with nothing chosen
inside it, it previews whole. It can be edited, deleted and copied as before; a
section cannot.

A file that opens with its one title, and nothing before it but blank lines or
front matter, is already named by that title: its subsections are the first
column. A file with fewer than two sections in all has no hierarchy to browse,
and opens as a plain file, as does one over the text size limit. A README with
one heading therefore behaves as it did.

The outline is computed by `ui/core/model/headings.js`, which runs without a
browser and is checked by `ui/core/model/test.mjs`. The adapter
`ui/adapters/vfs-doc.js` wraps the FS and PREVIEW ports the way
`vfs-json.js` does: sections are nodes, `FS.blob` answers a section with its
slice of the file, and `PREVIEW.render` renders that slice as the file's kind.
A node carries `doc` (a document) or `section` (a heading in one), and
`classifyFile` keeps a `doc` node's file kind although it has children.

The URL names a section by its heading text: `/guide.md/Install/Linux`.
The server accepts such paths for Markdown and reStructuredText files the way
it does for JSONL and CSV, and serves the shell; the client decides whether
the section exists. In the server edition, reStructuredText is rendered by
docutils on the server, so `/api/preview` takes `lines=START-END`, a 0-based,
end-exclusive line span, and renders that slice.

## Consequences

Entering a document with → opens its section column instead of focusing the
preview; a second → steps into it. README files still preview automatically
in their folder. Duplicate heading texts under one parent are suffixed
" (2)", " (3)" so that every row has one name. A section rendered on its own
lacks the definitions the rest of the file holds — footnotes, link references,
substitutions — which then render as plain text.

## Correction, 2026-10-11

Issue [80] fixes left-arrow navigation from a section column. The navigator
reselects the document or parent section in the column that receives focus.
It drops deeper section selections, so the preview and URL name that selection.
The selected document keeps its heading column open for right-arrow navigation.

[80]: ../tasks/80-left-arrow-doesn-t-preview-the-whole-document-after-returning-from-per.md

## Presentation correction, 2026-10-11

Issue [79] removes the section glyph from heading rows and folded columns.
Section previews omit the file summary heading and its divider. The selected
section name remains in the preview toolbar. The document's own heading starts
the content, in both rendered and source views. Whole-file previews keep their
file summary and edit control.

[79]: ../tasks/79-remove-signs-and-redundant-headings-from-document-section-previews.md

## Automatic preview correction, 2026-10-11

Automatic README and index preview selection applies to ordinary folders only.
Documents and sections preview their own full text when no child is selected.
Headings named `README`, `README.*`, or `index.html` do not change that selection.
This corrects review finding R1 for [80], including parent-section returns.
