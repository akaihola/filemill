# ADR 0034: Read-only (`mode: "read"`)

Date: 2026-08-16

## Supersession, 2026-10-19, issue [107]

The read-only application contract below is historical. Editing and deletion
now use `FS.write` and `FS.remove`, documented in `ui/core/ports.js` and
implemented by `ui/adapters/fsa.js`. They request `readwrite` permission when
needed. Picker calls in `ui/adapters/app-fsa.js` and `app-http.js` still use
`mode: "read"` for initial access; that does not make the application read-only.
See [static contributor guidance](../../static/AGENTS.md) and
`ui/editor/editor.js`. Preserve the original measurement below, but do not
remove writes or permission requests to restore it.

## Context

The static edition needs a documented decision for this design choice.

## Decision

Read-only (`mode: "read"`)

## Measurement

Nothing in the app writes, so never ask for write permission

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
