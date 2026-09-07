---
status: accepted
---

# Decide which finder owns interaction

## Proposal

The shared JavaScript finder owns clicks and navigation in both editions. The
server supplies API data and document previews. See
`docs/adr/0001-one-finder.md` for the decision and evidence.

## Evidence

The shared frontend is one source under `server/src/filemill/ui/`, and the
server exposes `/api/dir`, `/api/preview` and `/api/render`. The old HTMX
finder routes and implementation were removed in the completed cleanup work.

## Result

The decision is accepted and the duplicate finder has been removed. The
remaining no-JavaScript and embedding behaviour is a document-route concern,
not a second interactive finder.

## Scope

`server/src/filemill/{app.py,columns.py}`, `ui/core/{nav.js,shell.js,render.js}`,
and HTMX/shared-UI browser tests.
