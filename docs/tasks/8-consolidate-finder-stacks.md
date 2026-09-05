---
status: unverified
---

# Consolidate finder stacks

## Review proposal

Explore keeping `/api/*` plus `ui/` as the interactive finder and shrinking
HTMX to first-paint/no-JavaScript document pages, or explicitly choose the
reverse. Remove duplicated interaction behavior only after that decision.

## Evidence

`server/src/filemill/app.py` serves `/click` and HTMX columns alongside the
JavaScript finder backed by `/api/*`; breadcrumb, pruning, and folder/preview
branching exist in both stacks. The review marks this worth exploring, not
committed.

## Acceptance criteria

- The product decision records which stack owns interaction.
- First-paint, no-JavaScript, offline/embedded pages, breadcrumbs, folding,
  previews, and API routes retain their required behavior.
- Duplicate branches and their tests are removed only after coverage passes.

## Scope

`server/src/filemill/{app.py,columns.py}`, `ui/core/{nav.js,shell.js,render.js}`,
and HTMX/shared-UI browser tests.
