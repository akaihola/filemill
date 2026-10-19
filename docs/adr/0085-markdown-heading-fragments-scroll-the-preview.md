# 0085: Markdown heading fragments scroll the preview

Date: 2026-10-19

## Context

Section paths name a slice of a document. A heading fragment must instead open
that heading in the whole Markdown preview. Rendering is asynchronous, so the
browser's initial fragment lookup runs before the heading exists.

## Decision

Keep the heading IDs from markdown-it-anchor. Add a GitHub slug as a data
attribute on each heading. Allocate duplicate slugs in document order.
The path router exposes the encoded fragment as optional router state.
After preview rendering and font loading, the DOM renderer finds a GitHub alias
or an existing heading ID. It scrolls only the preview body and checks that the
preview is still current. Unknown or malformed fragments leave the file open.
The static edition keeps its existing fragment-based navigation format.

Keep server section routing in `api.split_vfs`. Its safe-path checks already
accept virtual paths after Markdown and reStructuredText files. The client
resolves headings. A missing section at any depth restores the whole file.

## Validation

HTTP tests cover nested and missing section paths. Browser tests load section
URLs directly for Markdown and reStructuredText. Fragment tests check the
preview scroll position for GitHub and existing renderer forms.
