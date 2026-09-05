---
depends-on: [33, 34]
---

# Reduce app.py to routing

## Goal

`server/src/filemill/app.py` contains the app object and its routes only.
No module imports another module inside a function. Roadmap phase 6, step 5.

## Steps

1. Do this after tasks [32], [33] and [34] have deleted the server-side
   renderers. What remains in `app.py` is: `_resolve_safe`, the symlink
   mount map, the shell, `/api/dir`, `/api/raw`, `/api/save`,
   `/api/preview` (pptx only), the resource route and the PWA routes.
2. Create `server/src/filemill/paths.py`. Move `_resolve_safe`, the symlink
   mount map and the root-relative URL helpers there.
3. Create `pwa.py`. Move `/manifest.json`, `/sw.js` and `/icons/` there.
4. Move the `/api/*` route functions into `api.py`, next to their helpers.
5. In `app.py`, keep the app object, the shell and the resource route.
6. Find imports inside functions:
   `grep -n "^    \+import \|^    \+from .* import" server/src/filemill/*.py`.
   Move each one to the top of its file. If that makes a cycle, move the
   needed function to `paths.py`.

## Done when

- The grep in step 6 prints nothing.
- `cd server && uv run pytest` passes.
- `wc -l server/src/filemill/app.py` is under 250.

## Scope

`server/src/filemill/`: `app.py`, `paths.py`, `pwa.py`, `api.py`.
