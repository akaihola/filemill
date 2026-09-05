---
status: unverified
depends-on: [6]
---

# Adapter-owned entry order

## Review proposal

Make ordering an adapter property: use one Python helper for `list_column` and
`dir_json`, with directories first and names compared by `casefold()`. HTTP
nodes trust that order; FSA nodes retain client-side ordering.

## Evidence

`columns.py:list_column` currently sorts inline by directory status and
lowercase name, while `api.py:dir_json` returns raw `iterdir()` order.
`ui/core/sort.js` sorts client-side, so the same directory can render in
different orders.

## Acceptance criteria

- A fixed fixture produces the documented order through `list_column` and
  `/api/dir`.
- HTTP name-order rendering does not re-sort the server result.
- FSA sorting and non-name metadata sorts continue to work.

## Scope

`server/src/filemill/{columns.py,api.py}`, HTTP/FSA adapters,
`server/src/filemill/ui/core/sort.js`, and server/browser tests.
