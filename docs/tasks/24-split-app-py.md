---
depends-on: [11]
---

# Split app.py into routing and helpers

## Goal

`server/src/filemill/app.py` contains routing only. No module imports another
module inside a function. Roadmap phase 6, step 1.

## Steps

1. Create `server/src/filemill/paths.py`. Move `_resolve_safe`, the symlink
   mount map, and the URL helpers there.
2. Create `routes_api.py`. Move the `/api/*` route functions there.
3. Create `routes_pages.py`. Move the HTML page routes there.
4. Create `pwa.py`. Move the manifest and service worker routes there.
5. In `app.py`, keep the app object and the `include_router` calls only.
6. Change `rendering.py` and `preview.py` to import from `paths`, not `app`.
7. Find imports inside functions:
   `grep -n "^    \+import \|^    \+from .* import" server/src/filemill/*.py`.
   Move each one to the top of the file. If that creates a cycle, move the
   needed function to `paths.py`.

## Done when

- The grep in step 7 prints nothing.
- `cd server && uv run pytest` passes.
- `wc -l server/src/filemill/app.py` is under 200.

## Scope

`server/src/filemill/`: `app.py`, `paths.py`, `routes_api.py`, `routes_pages.py`,
`pwa.py`, `rendering.py`, `preview.py`.
