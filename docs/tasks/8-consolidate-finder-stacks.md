---
status: unverified
---

# Decide which finder owns interaction

## Proposal

Filemill currently has two finder implementations. Decide which one handles
clicks and navigation. One option is to keep `/api/*` and `ui/` as the
interactive finder and keep HTMX only for the first page and no-JavaScript
document pages. The other option is to keep HTMX as the main finder.

Remove duplicate interaction code only after this decision.

## Evidence

`server/src/filemill/app.py` serves `/click` and HTMX columns. It also serves
the JavaScript finder through `/api/*`. Both implementations have breadcrumb
logic, column removal logic, and folder-versus-preview logic. The architecture
review says this idea needs more investigation. It is not a committed change.

## Acceptance criteria

- Record which finder owns interaction and why.
- Keep the required first page, no-JavaScript, offline, embedded-page,
  breadcrumb, folding, preview, and API behavior.
- Remove duplicate code only after tests cover the behavior that remains.

## Scope

`server/src/filemill/{app.py,columns.py}`, `ui/core/{nav.js,shell.js,render.js}`,
and HTMX/shared-UI browser tests.
