# 91. Server search stops at local-folder mounts

Date: 2026-10-20

Status: Accepted

## Context

The server edition can replace its served tree with a browser-owned folder.
Content search still queried the server tree after this switch. Its results
could call the absent path router. A queued input timer or a delayed response
could also restore results from the wrong tree. The user approved [120] as
an immediate fix. Shared search for both trees remains [130].

## Decision

The server adapter supplies a content-search function to the shared search
UI. It owns the API URL and response validation. The shared core owns the
query, focused path, result display and request cancellation.

Before a local mount changes the filesystem or router, remove the search
provider. Hide the form, disable and clear the input, remove all results,
cancel the input timer and abort the current request. Ignore late success
and error responses even if the transport completes after cancellation.
Invalidate the old result buttons too, so a retained button cannot navigate.

A served-tree mount supplies the provider again and starts with an empty
search. An old response stays invalid after this return. Submitting a search
also clears its queued input timer to avoid a duplicate request.

Hiding local search is temporary. This change adds no browser-owned content
search, new filesystem port or general navigation cancellation system.

## Validation

Browser coverage first failed with search still visible after a local mount.
The regression uses a controlled clock for queued input and explicitly releases
late responses. It checks the aborted signal, request counts, empty results,
disabled input, old result activation and working search after return.
Delayed success and error responses cannot replace local state. A response
released after return cannot replace a fresh served-tree result.

[120]: ../tasks/120-disable-server-search-in-local-folders-from-docs-question-5.md
[130]: ../tasks/130-give-served-and-browser-owned-folders-the-same-content-search.md
