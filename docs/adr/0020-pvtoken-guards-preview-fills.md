# ADR 0020: `pvToken` guards preview fills

Date: 2026-08-18

## Context

The static edition needs this design choice documented.

## Decision

`pvToken` guards preview fills

## Measurement

A slow read for a file you have navigated away from must not overwrite the current preview

## Consequences

The static edition follows this decision; the measurement guides maintenance and evaluation.

## Preview lifetime, 2026-10-21

[The preview reuse repair] retains one pane per current node, root, filesystem,
preview provider and content availability. Its key includes metadata values,
revision, representation, theme and the rich-renderer setting. Declining an outline
keeps the whole-file preview; the document's directory flag is not a content key.
Completed metadata reads update the key. Repeated layouts reuse pending fills
and completed DOM. A pending fill keeps its incoming revision while the provider
reads and populates the node's revision. Only the current fill publishes the
completed key. Metadata and mode changes still invalidate pending work.

Selection, metadata, refresh or mode changes replace or refill the pane.
Editor Save and Cancel refill it explicitly. A selection without preview advances
the token, preventing departed reads from painting the empty pane. Left-arrow removes preview focus explicitly, without replacing the focused
element. Object URLs survive resize and folding until pane replacement releases
them. Token guards still reject old fills. Unified asynchronous navigation generations
and separate object-URL ownership per concurrent provider read remain open A9 items.

[The preview reuse repair]: ../tasks/140-reuse-the-preview-element-across-resizes-and-folding.md
