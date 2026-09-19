---
status: completed
depends-on: [6]
---

# Use one rule for entry order

## Proposal

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
