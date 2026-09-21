---
depends-on: [30]
---

# Evaluate fully native toolkits

## Goal and scope

Compare AppKit, GTK and WinUI with the existing WebView prototype. Record
an evidence-backed recommendation in an ADR before any native toolkit work.
This task changes documentation only. The task brief of 2026-09-21 replaces
the earlier instruction to build and time a throwaway native column.

## Plan

1. Move only the unchanged [31] block to In Progress and commit this setup.
2. Compare columns, folding, previews, editing, accessibility, model reuse,
   performance, security, runtime dependencies and build costs. Use repository
   evidence and official toolkit documentation. Label unmeasured quantities.
3. Write an ADR under 40 lines with the comparison, recommendation, rejected
   options and gates for later work. Link it from the architecture review.
4. Run all pre-commit hooks, verify links and the complete diff against main.
   Removing [31] from each tracker must leave byte-identical remaining text.

## Baseline constraint

The brief calls [30] complete. The repository still records it as In Progress
with an unqualified WebKitGTK host. Use that result without claiming native
UI parity or changing [30]. See [ADR 0065](../adr/0065-native-shell-qualification.md).
Do not implement a toolkit or repair the prototype in this task.
