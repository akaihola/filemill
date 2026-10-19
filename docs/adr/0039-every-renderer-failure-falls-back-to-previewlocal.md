# ADR 0039: Every renderer failure falls back to `PreviewLocal`

Date: 2026-08-30

## Status update, 2026-10-19, issue [109]

The decision holds through the renderer registry, not `PreviewLocal`. Since
`ea0a3dbe`, a Markdown, reStructuredText or DOCX renderer that throws falls
back to the `offline` entry in `ui/adapters/preview-rich.js`. That entry draws
the core text renderer's raw `<pre>` with the offline note, or nothing for a
binary. PPTX needs no download; a file it cannot read shows an error message.

## Context

The static edition needs a documented decision for this design choice.

## Decision

Every renderer failure falls back to `PreviewLocal`

## Measurement

Offline must be a loss of fidelity, not a broken pane: raw `<pre>` with a one-line note, or nothing for a binary

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.

[109]: ../tasks/109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md
