# ADR 0014: A sweep repaints only while its node is still in `path`

Date: 2026-08-18

## Context

The static edition needs a documented decision for this design choice.

## Decision

A sweep repaints only while its node is still in `path`

## Measurement

It can outlive the column that started it. What it read is kept either way, because a file's size is a fact about that file and stepping back into the folder finds it there

## Consequences

The static edition follows this decision. The measurement above records the basis for maintaining and evaluating it.
