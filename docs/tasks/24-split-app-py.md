---
depends-on: [33, 34]
---

# Reduce app.py to routing

## Goal

`server/src/filemill/app.py` contains the app object, the shell and its routes
only. No module imports another module inside a function. Roadmap phase 6,
step 5.

## Steps

1. Do this after tasks [33] and [34] have deleted the server-side renderers.
2. Create `server/src/filemill/paths.py`. Move `_resolve_safe` and the symlink
   mount map there as `resolve_safe`, `mount_targets` and `resolve_web_mount`.
   Each takes the root explicitly; `app.py` keeps the `ROOT` global (tests and
   `cli.py` set it there) and a one-argument `_resolve` adapter for the routes
   and for `api.split_vfs`.
3. Create `pwa.py` with `STATIC_DIR`, `SW_REGISTER_JS` and the handlers for
   `/manifest.json`, `/sw.js` and `/icons/`. `app.py` registers them with
   `rt(...)(handler)`, so `pwa.py` never imports the app.
4. Delete `_mounted_path_parts` and `_rel_url_path`: nothing calls them.
5. Find imports inside functions:
   `grep -rn "^\s\+\(from\|import\) " server/src/filemill/ --include=*.py`.
   Move each one to the top of its file.

## Done when

- The grep in step 5 prints nothing.
- `cd server && uv run pytest` passes.

## Scope

`server/src/filemill/`: `app.py`, `paths.py`, `pwa.py`, `cli.py`,
`preview.py`, `providers/json_provider.py`, and the server tests that import
the moved names.
