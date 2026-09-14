# ADR 0059: The chain is stored as names, not nodes

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

The chain is stored as names, not nodes

## Measurement

A node comes from a read that has not happened when the page loads. A name outlives a reload, a rename of its parent, and the node cache

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
