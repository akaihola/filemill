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
