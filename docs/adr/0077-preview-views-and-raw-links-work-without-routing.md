# ADR 0077: Preview views and Raw links work without routing

Date: 2026-10-11.

## Context

Issue [89] removed duplicate Markdown and WebVTT controls. Its independent
review found that the surviving toggle required a router, which the server's
local-folder mode disables. Static previews also ignored Source because only
the server wrapped its providers with source highlighting. The Raw link was
absent without a router and used a server path with the static hash router.

## Decision

Keep the preview representation in `data-filemill`. A router records changes
when available; it does not enable them. Share the existing `withHighlighting`
wrapper between both editions instead of restoring per-type toolbar groups.

Move raw URL construction to the filesystem adapter's optional `rawURL(node)`
capability. Without it, core reads through `FS.blob`, creates an object URL,
and opens Raw in a new tab. Untyped blobs use `text/plain`. Core revokes its
raw object URL on preview replacement or view change and checks the preview
generation before exposing bytes from an asynchronous read.

## Consequences

Markdown and WebVTT retain one Raw control and a working Source/Rendered
toggle in the server, its local-folder mode, the static bundle and the static
module build. Local view changes preserve the address bar; static view links
retain the root folder name. Served Raw links keep their existing file URLs.
The local Raw read adds no network request or dependency.

[89]: ../tasks/89-markdown-previews-show-two-raw-buttons.md
