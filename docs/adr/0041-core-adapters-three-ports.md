# ADR 0041: `core/` + `adapters/`, three ports

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

`core/` + `adapters/`, three ports

## Measurement

The same UI runs over the File System Access API and over a server. filemill browses with `core/` untouched, which is the only way two apps stay identical — a copied UI diverges one bug fix at a time

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.

## Refresh invalidation, 2026-10-21

FS has an optional `invalidate(node)` hook. Core waits for an active load,
clears the common listing state, awaits this hook, then calls `ensureLoaded`.
The hook owns adapter caches. It does not introduce a second listing writer.

The JSON adapter discards the parsed source, cached file bytes, size metadata
and prior parse errors. It reads the current file or archive member through
its backing FS port. A nested JSON column resolves its structural path from
that new source. The existing selection walk closes removed paths and the
existing render updates the preview. Invalid input shows a parse error and
source text; it cannot retain a previous parsed value.

This contract applies to the shared static, development and served UI.
It keeps the navigation sequence and preview token guards. The broader
navigation and preview ownership work remains in [A9].

[A9]: ../ARCHITECTURE-REVIEW.md#a9-preview-reuse-and-async-ownership-remain-missing
