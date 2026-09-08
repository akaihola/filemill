# ADR 0001: Use one shared JavaScript finder

Status: accepted

## Context

Filemill had two finder implementations. The HTMX finder and the JavaScript
finder both handled directory navigation, breadcrumbs, column changes and
previews. A change to one finder could leave the other finder different.

The static edition needs a browser finder for local folders. The server edition
needs a finder for files and virtual filesystems served by its API. The server
also needs to render documents when its Python renderers provide the result.

## Alternatives

1. Keep HTMX as the main finder. The server would continue to build columns and
   interaction responses. The static edition would need a separate finder.
2. Keep both finders. HTMX could serve the first page and no-JavaScript or
   embedded document pages. This keeps two interaction models and their
   duplicate rules.
3. Use one shared JavaScript finder. Give it a filesystem, preview and router
   port. The static edition supplies local adapters. The server edition supplies
   HTTP adapters and keeps document rendering on the server.

## Decision

Choose the shared JavaScript finder. It owns selection, navigation, columns,
folding, breadcrumbs, previews and URL state in both editions.

The server supplies directory data through `GET /api/dir`, previews through
`GET /api/preview`, and rendering for local bytes through `POST /api/render`.
The server still handles path safety, virtual filesystem providers and Python
document renderers. The `layout=no-columns` document route uses the shared
shell when a document needs the application view.

## Measurement

The shared frontend is one source under `server/src/filemill/ui/`; the root
`ui/` path points to it. The server shared-frontend work added 68 tests in
`test_api.py` and `test_browser_new_ui.py`. The server task record reports 56
browser tests passing after the browser-suite repair. The completed HTMX
cleanup removed its dead routes, column generator, JavaScript blob and
HTMX-only tests. These results show that both editions can use the same
interaction code while the server keeps its existing API and renderers.

## Consequences

- A navigation or interaction rule has one implementation and one test target.
- The static and server editions share the core UI and differ through adapters.
- The server remains responsible for safe paths, directory and virtual-file
  data, and document rendering.
- A browser is required for the interactive finder. A no-JavaScript document
  page must use a separate simple route or an embedding contract; it is not a
  second finder.
- Server browser tests exercise the shared UI through the HTTP adapters, while
  static tests exercise the local adapters. Adapter failures can still differ.
- Removing the old finder reduces maintenance work, but changes to the shared
  UI affect both editions and must be checked in both environments.
