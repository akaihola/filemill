# ADR 0036: …but behind a remembered switch, defaulting on

Date: 2026-08-16

## Scope note, 2026-10-19, issue [109]

The switch governs downloads from a third-party CDN. A module served from the
Filemill origin bypasses it (`vendored()` in `ui/adapters/preview-rich.js`),
so in the server edition it changes no Markdown or DOCX preview. The renderers
are not the only network use either: a document can reference resources such
as images. See the
[static edition notes](../../README.md#static--one-file-no-server-no-install).

## Context

The static edition needs a documented decision for this design choice.

## Decision

…but behind a remembered switch, defaulting on

## Measurement

It is the only thing here that talks to the network, and the pitch is that your folder does not. Consent that resets every reload is not consent. Nothing about the file is ever *sent* — the request is for the library

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.

[109]: ../tasks/109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md
