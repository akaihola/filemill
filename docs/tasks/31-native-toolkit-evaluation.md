---
depends-on: [30]
---

# Evaluate fully native toolkits

## Goal

We know whether AppKit, GTK or WinUI can replace the WebView shell, and at
what cost. The answer is written down. Roadmap phase 9, step 3.

## Steps

1. For each toolkit, write a five-line list: how it draws Miller columns,
   how it does a folding animation, how it renders Markdown and highlighted
   text, how it shows a PDF, and how big the runtime is.
2. Build one column with folding in one toolkit on the machine you have.
   Time the work in hours.
3. Write `docs/adr/NNNN-native-toolkits.md`. Put the five-line lists in
   `## Context`, the build time and the runtime sizes in `## Measurement`, and
   a decision in `## Decision`: keep the WebView shell, or start one native
   port and which one.

## Done when

- The ADR exists and is under 40 lines.
- No native toolkit code is in the tree unless the ADR says to start one.

## Scope

`docs/adr/`. A throwaway prototype outside the repository.
