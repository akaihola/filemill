# ADR 0043: Hash URLs in the static build, path URLs on the server

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

Hash URLs in the static build, path URLs on the server

## Measurement

A hash survives `file://`, a bare `http.server`, and any static host — none of which can rewrite paths. The server has a root, so its URL path can mirror the file path exactly

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
