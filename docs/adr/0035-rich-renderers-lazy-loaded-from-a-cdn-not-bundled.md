# ADR 0035: Rich renderers lazy-loaded from a CDN, not bundled

Date: 2026-08-16

## Scope note, 2026-10-19, issue [109]

This decision holds for the static edition and the native shell. Since
`59672dd6` (issue [32]), the server edition serves the Markdown and DOCX
modules from `/ui/vendor/` (`FILEMILL_CDN` in `server/src/filemill/app.py`) and
renders reStructuredText on the server. Since `90f40ed3`, no edition downloads
a PPTX renderer.

## Context

The static edition needs a documented decision for this design choice.

## Decision

Rich renderers lazy-loaded from a CDN, not bundled

## Measurement

markdown-it + plugins + mammoth are ~1 MB against the app's 140 KB. Fetching them on first use keeps the single file portable and gives it filemill's rendering

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.

[109]: ../tasks/109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md
[32]: ../tasks/32-browser-markdown-in-server-edition.md
