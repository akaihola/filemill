# ADR 0044: `#r=<root>` names the folder, matched against the remembered roots

Date: 2026-08-16

## Context

The static edition needs a documented decision for this design choice.

## Decision

`#r=<root>` names the folder, matched against the remembered roots

## Measurement

A `FileSystemDirectoryHandle` is not a path: the URL cannot name a folder the browser has not already granted, and a page that could name arbitrary directories would be worse

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
