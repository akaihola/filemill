# Implementation Plan – Gogo dashboard integration

## Scope

Adapt Pykofinder’s FastHTML/ASGI app for embedding in the gogo dashboard while preserving standalone behavior. This is a plan only; no production implementation belongs in this change.

## Current integration points

- `src/pykofinder/app.py`: `/click`, `/raw`, `/w/{path:path}`, `/f/`, `/f/{path:path}`, `_resolve_safe()`, mount URL helpers, shell/deep-navigation JavaScript.
- `src/pykofinder/columns.py`: Finder links, HTMX targets, `data-finder-url`, breadcrumb.
- `src/pykofinder/preview.py`: Markdown dispatch, Pygments code dispatch, UTF-8 raw fallback, PDF/image `/raw` URLs.
- `src/pykofinder/rendering.py`: Markdown links/wikilinks and current `/f/`, `/w/`, or `/raw?path=` URL generation.
- Existing tests cover mount URLs, legacy absolute-path query URLs, safety zones/symlinks, Markdown, syntax highlighting, raw fallback, preview routes, HTMX fragments, and deep-link restoration.

## Required behavior

### 1. Dashboard view query propagation

Introduce one URL/query contract for the dashboard view selector:

- Internal navigation links and generated URLs preserve `view=pykofinder`.
- Preserve it across Finder links, Markdown links/wikilinks, breadcrumb/deep-navigation URLs, HTML “View as web page” links where applicable, raw-file switch links, and redirects from legacy `/f/?path=`.
- Treat only the exact supported view value as meaningful; ignore unsupported values rather than reflecting arbitrary query data into HTML.
- Use proper query encoding; avoid double-encoding path/vpath values. Keep `vpath` intact for VFS deep links.

Define a small shared URL-builder/query helper rather than hand-concatenating `view` at each call site. Apply HTML escaping at output boundaries.

### 2. Arbitrary absolute paths

Support dashboard requests for arbitrary paths under `/home/agent` (and configured roots) without requiring named `/w/<mount>/` or `/f/<mount>/` prefixes:

- Add/extend a canonical dashboard-compatible route contract accepting an absolute path query parameter, using the existing `/f/?path=` and `/raw?path=` concepts where compatible.
- Render the full Finder shell/deep navigation for a valid absolute file or directory.
- Serve raw bytes for a valid absolute file through the raw route.
- Keep named-mount `/w/` and `/f/` routes backward-compatible.
- For paths without a named mount, generate the supported absolute-path query contract; never fabricate a mount prefix.
- Never expose an absolute filesystem path in a route without resolving and validating it first.

### 3. Raw-file/router integration assumptions

Document and implement the gogo router contract:

- Router-facing raw requests are GET-only and return a file response with detected media type; directories/missing/denied targets return 404.
- Rendered endpoints return HTML fragments or the full shell as specified; raw bytes must not fall through FastHTML’s catch-all.
- Preserve query parameters when the dashboard router forwards or rewrites requests.
- Keep route ordering explicit so PWA/static routes, raw files, Finder routes, and the catch-all do not shadow one another.
- Preserve existing `/w/` CORS behavior only for web-static requests.
- Test direct TestClient requests and generated href/src values.

### 4. Rendered Markdown and syntax-highlighted views

- Markdown defaults to rendered HTML through `rendering.md`, retaining relative links, wikilinks, linkify, Mermaid, and escaping.
- Source/code files default to syntax-highlighted Pygments HTML within `preview-code`, retaining current size/encoding fallbacks.
- Add a query/format switch for rendered versus raw source where gogo needs it.
- Rendered Markdown links continue to point to Finder views and preserve `view=pykofinder`; non-Markdown assets use the raw-file contract.
- Keep unsupported, binary, and large-file behavior explicit.
- Reuse existing Markdown/Pygments pipelines rather than duplicating them.

### 5. Raw-file switch link contract

Define stable controls emitted with rendered Markdown and syntax-highlighted source:

- A visible switch link/button has a stable class or data attribute and links to the same file’s raw view.
- It preserves `view=pykofinder` and applicable `vpath`; it uses named `/w/` only when mounted and the absolute-path raw contract otherwise.
- The raw view has a reciprocal link to the rendered Finder view.
- Embedded raw content is escaped; direct raw responses remain bytes with correct Content-Type.
- Tests assert exact path/query semantics, not merely that an href contains `/raw`.

## Safety and query rules

- All filesystem inputs pass `_resolve_safe()` after URL decoding and normalization; containment is checked on resolved paths.
- Preserve the existing allowed zones: configured ROOT and direct-symlink bookmark targets, including permitted descendants. Deny traversal, unknown mounts, outside paths, broken links, directories on file-only endpoints, and missing paths.
- Validate absolute-path query values before rendering, redirecting, or link construction. Never use unvalidated input in `Path`, `FileResponse`, HTML, or JavaScript.
- Cover direct bookmark targets and nested symlinks escaping the allowed zone.
- Define deterministic behavior for absent, empty, repeated, malformed, and encoded `path`, `view`, `vpath`, and mode parameters; test it.
- Preserve `view=pykofinder` through redirects and generated URLs without allowing query values to bypass containment.
- Escape path-derived HTML/JSON-script values and encode each URL query value exactly once.
- Avoid open redirects: generated links are local, except approved external `.desktop` destinations.
- Return 404 for denied paths without revealing whether an outside target exists.

## Planned file changes

- `src/pykofinder/app.py`: shared URL/query parsing/building; dashboard absolute-path routes; raw/rendered mode dispatch; route ordering and view propagation.
- `src/pykofinder/columns.py`: add `view=pykofinder` to internal links and deep-navigation metadata without breaking HTMX targets.
- `src/pykofinder/preview.py`: explicit rendered/raw mode, switch markup, Markdown/code integration, reciprocal links, and existing fallbacks.
- `src/pykofinder/rendering.py`: pass view/query context into Markdown and wikilink hrefs; retain relative-link and mount fallback behavior.
- `src/pykofinder/styles.py`: only minimal switch-control CSS if existing preview-bar styles cannot be reused.
- `README.md`, `CONTRIBUTING.md`, `ISSUES.md`, `TASKS.md`: document and track the gogo URL/router contract.
- Tests: extend `test_app.py`, `test_routes_new.py`, `test_resolve_safe.py`, `test_columns.py`, `test_preview.py`, and `test_rendering.py`; add a focused integration module only if clearer.

## TDD implementation order

1. Add issue/task tracking and failing tests for query propagation, absolute-path shell/raw access, denied paths, query edge cases, and raw-switch markup.
2. Add shared URL/query helpers and make existing URL generators preserve `view`; run focused URL/link tests.
3. Add dashboard-compatible absolute-path route handling and raw response contract; run route/safety tests.
4. Add explicit rendered/raw preview mode and reciprocal switch links; run preview/rendering tests.
5. Update deep-navigation/history code and required CSS; run JavaScript-string/rendering tests.
6. Run `timeout 120 uv run pytest`.
7. Update documentation/tracking, review for route/security regressions, and commit logical changes conventionally.

## Acceptance tests

- Every internal generated link retains `view=pykofinder`, including redirects, Markdown/VFS links, raw/rendered switches, and deep navigation.
- A valid `/home/agent/...` absolute path renders or serves without `/w/` or `/f/` prefixes.
- Named mounts remain backward-compatible.
- Traversal, outside-root, unsafe symlink, unknown mount, missing, and directory-as-file requests return 404.
- Raw responses have correct content type and no HTML wrapper; rendered responses retain preview classes and escaping.
- Markdown and recognized source files use existing pipelines; raw switches are reciprocal and query-preserving.
- Repeated/malformed/encoded queries have deterministic tested behavior.
- The full suite passes under the documented timeout.
