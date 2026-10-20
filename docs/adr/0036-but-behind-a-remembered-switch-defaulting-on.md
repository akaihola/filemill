# ADR 0036: Remember rich-preview consent

Date: 2026-08-16

## Context

The static edition downloads rich-preview libraries from a third-party CDN.
Consent must survive reloads. The request fetches a library; it sends no file.

## Decision

Put CDN renderer downloads behind a remembered switch, defaulting on.

## Measurement

The original basis was that renderer downloads were the only network use.
[109] corrected that claim on 2026-10-19: documents can request images and
other resources. The switch controls renderer downloads only.

## Consequences

Same-origin modules bypass consent through `vendored()` in the
[rich-preview adapter]. A stored `filemill.rich=off` does not disable the
server's vendored Markdown or DOCX previews. See the [static edition notes].

## Visibility update, 2026-10-20

[118] shows the switch only after renderer registration, when a required
module uses a third-party CDN. Static and native retain remembered, default-on
consent. The server hides the switch, heading and separator in served and
Open Folder modes: Markdown/DOCX use vendored modules and PPTX extracts text
without a download. Python handles served RST; local-folder RST is unchanged.

[rich-preview adapter]: ../../ui/adapters/preview-rich.js
[static edition notes]: ../../README.md#static--one-file-no-server-no-install
[109]: ../tasks/109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md
[118]: ../tasks/118-hide-the-ineffective-server-preview-switch-from-docs-question-3.md
