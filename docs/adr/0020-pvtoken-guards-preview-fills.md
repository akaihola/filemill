# ADR 0020: `pvToken` guards preview fills

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

`pvToken` guards preview fills

## Measurement

A slow read for a file you have navigated away from must not overwrite the current preview

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.

## Preview lifetime, 2026-10-21

[The preview reuse repair] retains one pane for the current node, root,
filesystem, preview provider and content availability. Its key includes metadata values, revision,
representation, theme and the rich-renderer setting. A document that declines
its outline keeps its whole-file preview; its directory flag is not a content key.
Metadata reads update the key after they finish. Repeated layout renders
reuse both a pending fill and its completed DOM. A pending fill holds its
incoming revision while the provider reads and populates the node's revision.
Only the current fill publishes the completed key. Metadata and mode changes
still invalidate pending work.

A new selection, metadata change, refresh or mode change replaces or refills
the pane. Editor Save and Cancel refill it explicitly. A selection with no
preview also advances the token, so a departed read cannot paint the empty
pane. Left-arrow explicitly removes focus from the preview; it no longer
depends on replacing the focused element. Object URLs stay valid through resize and folding and are released
when the pane is replaced. The existing token guards still reject old fills.
This decision does not unify asynchronous navigation generations or give
each concurrent provider read separate object-URL ownership. Those A9 items
remain open.

[The preview reuse repair]: ../tasks/140-reuse-the-preview-element-across-resizes-and-folding.md
