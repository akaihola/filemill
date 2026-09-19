---
status: completed
depends-on: [6]
---

# Use one rule for entry order

## Delivered contract

Commits `c10c1e3` and `9e46ede` implement adapter-owned ordering. HTTP orders
entries on the server; File System Access orders them while loading. Both put
directories first, then case-insensitive names with the adapter's tie-breaker.
`node.ordered` preserves that order for name sorting; size and modified-time
sorting still use the shared sorter. See the [adapter contract](../../ui/adapters/README.md).

The proposal below predates that contract and the removal of `columns.py`.
It records the original rationale and acceptance criteria.

## Original proposal

Use one Python helper to order entries for both `list_column` and `dir_json`.
Put directories first. Compare names with `casefold()` so upper- and
lowercase names sort consistently.

The HTTP adapter should keep this order. The File System Access adapter should
keep its own client-side sorting because it reads entries locally.

## Evidence

`columns.py:list_column` currently sorts entries by directory status and
lowercase name. `api.py:dir_json` returns the order from `iterdir()` without
sorting it. `ui/core/sort.js` sorts entries in the browser. As a result, the
same directory can appear in different orders.

## Acceptance criteria

- A fixed test directory produces the documented order through `list_column`
  and `/api/dir`.
- HTTP name sorting keeps the server order.
- File System Access sorting still works for names and for metadata such as
  size and modified time.

## Scope

`server/src/filemill/{columns.py,api.py}`, HTTP/FSA adapters,
`server/src/filemill/ui/core/sort.js`, and server/browser tests.
