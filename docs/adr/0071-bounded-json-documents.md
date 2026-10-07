# ADR 0071: JSON documents have a separate size limit

Date: 2026-10-07

## Context

The JSON virtual filesystem used the 512 KiB text preview limit. This rejected
a valid 540,588-byte backup manifest. JSON already has a shared browser adapter
for parsing, nested columns and foldable previews in both editions.

## Decision

Set `JSON_MAX` to 8 MiB in `ui/core/limits.js`. Keep `TEXT_MAX` at 512 KiB for
ordinary text. JSON objects, arrays and scalars up to `JSON_MAX` use the existing
JSON adapter and preview. Do not truncate a JSON document.

Reject a document above the limit before `FS.blob` when listing metadata gives
its size. Check the returned blob size again before reading its text. Show the
size limit in the preview pane. Invalid JSON keeps the colored-source fallback.

Allow JSON virtual paths through the server's existing browser-owned path
contract. Resolve the real file with the normal containment checks. Let the
browser validate its nested keys, as it already does for JSONL records.

## Consequences

The adapter still parses the entire accepted document and keeps its value.
The size limit bounds that input, but does not bound nesting depth or rendered
DOM size. Streaming arbitrary JSON and range reads need a separate measured
case. JSONL keeps its existing lazy line index.

This decision replaces the JSON size rule in
[ADR 0038](0038-a-text-preview-is-whole-or-absent-text-max-512-kb-is-the-only-limit.md).
