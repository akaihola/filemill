# ADR 0068: A large JSONL file is indexed by line, not parsed whole

Status: accepted, 2026-09-19.

## Context

A `.jsonl` file opened as a column of rows. `ui/adapters/vfs-json.js` read the
whole file as text, split it into lines, parsed every line, scanned every record
to choose a label key, and kept one parsed value per row. That work grows with
the file, so the adapter declined any file over `TEXT_MAX` (512 KB) with the
note `Too large to browse`. [ADR 0038](0038-a-text-preview-is-whole-or-absent-text-max-512-kb-is-the-only-limit.md)
made `TEXT_MAX` the one limit for a text preview. A JSONL file is not a text
preview: it is a directory of records, and a directory does not need every
record in memory to list its names.

## Decision

A `.jsonl` file up to `TEXT_MAX` keeps the eager path: rows named by a unique
key, the whole file validated on open.

A `.jsonl` file over `TEXT_MAX` has no ceiling. The adapter makes one pass over
`blob.stream()` and records the byte span of each non-blank line. It does not
decode the file into a string and does not parse any record. Each row is named
`line N`, the label the eager path already uses when no key can name every row,
so selection, deep links and `applyPath` keep the same contract. A row's span is
parsed from `blob.slice()` only when the user opens or previews that row. A
line that is not a JSON object fails on its own row: the row becomes a leaf
whose preview reports `Not valid JSONL: line N`, and every other row stays
browsable.

No third-party library. A streaming JSON parser would still parse every record,
which is the cost this decision avoids. `Blob.stream()` and `Blob.slice()` are
enough.

## Consequences

- Memory for an open large file is the browser-managed `Blob` plus two numbers
  per line. Row nodes carry no value until read.
- The column virtualises rows from 1 000 entries, so a file with many lines
  renders at the cost of one screen of rows.
- The server edition still transfers the whole file once through `FS.blob`.
  Range reads would need a port change and are out of scope.
- Labels change from key-named to `line N` at the `TEXT_MAX` boundary.
