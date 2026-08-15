# Implementation Plan – Gogo dashboard integration

## Scope

Adapt Pykofinder’s FastHTML/ASGI app for embedding in the gogo dashboard while preserving standalone behavior. This is a plan only; no production implementation belongs in this change.

The URL path is always the file path relative to the configured root. Query
parameters select the representation and layout; they do not carry an absolute
filesystem path.

## Current integration points

- `src/pykofinder/app.py`: `/click`, `/raw`, `/w/{path:path}`, `/f/`, `/f/{path:path}`, `_resolve_safe()`, mount URL helpers, shell/deep-navigation JavaScript.
- `src/pykofinder/columns.py`: Finder links, HTMX targets, `data-finder-url`, breadcrumb.
- `src/pykofinder/preview.py`: Markdown dispatch, Pygments code dispatch, UTF-8 raw fallback, PDF/image `/raw` URLs.
- `src/pykofinder/rendering.py`: Markdown links/wikilinks and current `/f/`, `/w/`, or `/raw?path=` URL generation.
- Existing tests cover mount URLs, legacy absolute-path query URLs, safety zones/symlinks, Markdown, syntax highlighting, raw fallback, preview routes, HTMX fragments, and deep-link restoration.

## Required behavior

### 1. URL and query contract

Use the same path for all representations. For a configured root containing
`docs/readme.md`:

- `/docs/readme.md` serves the static file by default.
- `/docs/readme.md?pykofinder-view=rendered` serves the rendered view.
- `/docs/readme.md?pykofinder-view=highlighted` serves the syntax-highlighted view.
- `/docs/readme.md?pykofinder-view=raw` serves the raw view.
- `layout=full-columns`, `layout=compressed-columns`, or `layout=no-columns`
  selects the Finder layout.
- `hidden=show` or `hidden=hide` selects dotfile visibility.
- Missing or invalid query values use documented defaults and never change the
  requested file path.

Internal links preserve the current file path and query state where relevant.
Use one shared query parser and URL builder. Encode query values once and apply
HTML escaping at output boundaries.

### 2. Relative file paths

Serve paths relative to the configured root without requiring `/w/<mount>/` or
`/f/<mount>/` prefixes:

- `/relative/path` serves the file at `ROOT / relative/path` as a static file.
- The same path with `pykofinder-view=rendered`, `highlighted`, or `raw` selects
  the matching representation.
- Directory paths render the selected column layout when the Pykofinder view is
  requested.
- Keep named-mount `/w/` and `/f/` routes only as legacy compatibility routes,
  if they are still needed by existing callers.
- Never accept an absolute filesystem path from the client as the canonical
  route format.

### 3. Raw-file/router integration assumptions

Document and implement the gogo router contract:

- Router-facing static/raw requests are GET-only and return a file response
  with detected media type; directories/missing/denied targets return 404.
- Rendered endpoints return HTML fragments or the full shell as specified; raw bytes must not fall through FastHTML’s catch-all.
- Preserve `pykofinder-view`, `layout`, and `hidden` when the dashboard router
  forwards or rewrites requests.
- Keep route ordering explicit so PWA/static routes, raw files, Finder routes, and the catch-all do not shadow one another.
- Preserve existing `/w/` CORS behavior only for web-static requests.
- Test direct TestClient requests and generated href/src values.

### 4. Rendered Markdown and syntax-highlighted views

- Markdown uses `pykofinder-view=rendered`; source/code uses
  `pykofinder-view=highlighted`. `pykofinder-view=raw` returns the source.
- Keep relative links, wikilinks, linkify, Mermaid, escaping, size limits, and
  encoding fallbacks.
- Rendered Markdown links keep the same relative URL path and add the required
  `pykofinder-view` value. Non-Markdown assets use the same path with the raw
  view when a representation switch is needed.
- Keep unsupported, binary, and large-file behavior explicit.
- Reuse existing Markdown/Pygments pipelines rather than duplicating them.

### 5. Raw-file switch link contract

Define stable controls emitted with rendered Markdown and syntax-highlighted source:

- A visible switch link/button has a stable class or data attribute and links to
  the same path with `pykofinder-view=rendered`, `highlighted`, or `raw`.
- It preserves `layout`, `hidden`, and applicable `vpath`.
- The raw view has a reciprocal link to the matching rendered or highlighted
  view.
- Embedded raw content is escaped; direct raw responses remain bytes with correct Content-Type.
- Tests assert exact path/query semantics, not merely that an href contains `/raw`.

## Safety and query rules

- All filesystem inputs pass `_resolve_safe()` after URL decoding and normalization; containment is checked on resolved paths.
- Preserve the existing allowed zones: configured ROOT and direct-symlink bookmark targets, including permitted descendants. Deny traversal, unknown mounts, outside paths, broken links, directories on file-only endpoints, and missing paths.
- Validate the root-relative route path before rendering, redirecting, or link
  construction. Never use an unvalidated path in `Path`, `FileResponse`, HTML,
  or JavaScript.
- Cover direct bookmark targets and nested symlinks escaping the allowed zone.
- Define deterministic behavior for absent, empty, repeated, malformed, and
  encoded route paths, `pykofinder-view`, `layout`, `hidden`, and any VFS
  `vpath` parameters; test it.
- Preserve valid `pykofinder-view`, `layout`, and `hidden` values through
  redirects and generated URLs without allowing query values to bypass
  containment.
- Escape path-derived HTML/JSON-script values and encode each URL query value exactly once.
- Avoid open redirects: generated links are local, except approved external `.desktop` destinations.
- Return 404 for denied paths without revealing whether an outside target exists.

## Planned file changes

- `src/pykofinder/app.py`: shared URL/query parsing/building; root-relative
  routes; static/raw/rendered mode dispatch; route ordering and query
  propagation.
- `src/pykofinder/columns.py`: preserve layout/hidden state in internal links
  and deep-navigation metadata without breaking HTMX targets.
- `src/pykofinder/preview.py`: explicit rendered/raw mode, switch markup, Markdown/code integration, reciprocal links, and existing fallbacks.
- `src/pykofinder/rendering.py`: pass view/query context into Markdown and wikilink hrefs; retain relative-link and mount fallback behavior.
- `src/pykofinder/styles.py`: only minimal switch-control CSS if existing preview-bar styles cannot be reused.
- `README.md`, `CONTRIBUTING.md`, `ISSUES.md`, `TASKS.md`: document and track the gogo URL/router contract.
- Tests: extend `test_app.py`, `test_routes_new.py`, `test_resolve_safe.py`, `test_columns.py`, `test_preview.py`, and `test_rendering.py`; add a focused integration module only if clearer.

## TDD implementation order

1. Add issue/task tracking and failing tests for root-relative static paths,
   query modes, layout/hidden state, denied paths, query edge cases, and
   raw-switch markup.
2. Add shared URL/query helpers and preserve the three query groups; run
   focused URL/link tests.
3. Add root-relative route handling and static/raw response contracts; run
   route/safety tests.
4. Add explicit rendered/highlighted/raw preview modes and reciprocal switch
   links; run preview/rendering tests.
5. Update deep-navigation/history code and required CSS; run JavaScript-string/rendering tests.
6. Run `timeout 120 uv run pytest`.
7. Update documentation/tracking, review for route/security regressions, and commit logical changes conventionally.

## Acceptance tests

- Every internal generated link keeps the same root-relative path and valid
  `pykofinder-view`, `layout`, and `hidden` query values.
- A valid root-relative path serves statically by default and selects the
  requested representation with query parameters.
- Named mounts remain backward-compatible where required.
- Traversal, outside-root, unsafe symlink, unknown mount, missing, and directory-as-file requests return 404.
- Raw responses have correct content type and no HTML wrapper; rendered responses retain preview classes and escaping.
- Markdown and recognized source files use existing pipelines; raw switches are
  reciprocal and query-preserving.
- Repeated/malformed/encoded queries have deterministic tested behavior.
- The full suite passes under the documented timeout.
