---
depends-on: [32]
---

# Decide the fate of the /w/ named mounts

## Goal

The `/w/<mount>/...` route and its CORS middleware in `app.py` either have a
documented consumer or are gone. Roadmap phase 6, step 4.

## Background

`/w/` serves files under the root and under each symlink child of the root.
Until this issue it also sent `Access-Control-Allow-Origin: *` on every
response. `rendering.py` used the route for Markdown links to files outside
the root; task [32] deleted `rendering.py`.

`git grep -n "/w/" -- ui server/src docs README.md` finds one consumer:
`homeHref` in `ui/adapters/preview-rich.js` rewrites a Markdown `~/x` link to
`/w/<root-name>/x`. That page is served by the same origin, so it never needs
CORS. Nothing on the gogo dashboard, in `~/menu`, or in a systemd unit loads a
`/w/` URL from another origin.

## Decision

Keep `/w/` as the one same-origin static mount. Delete the CORS middleware,
its headers and its tests; there is no consumer to make an opt-in option for.
`SECURITY.md` documents the route and the no-CORS default. Anyone who needs
cross-origin reads puts a reverse proxy in front of a trusted bind.

`_web_url` had no callers and went with the middleware. The standalone-mount
fallback in `_mounted_path_parts` only fed `_web_url`; removing it belongs to
the `app.py` refactor in [24].

## Done when

- `grep -n "CORS\|_web_url" server/src/filemill/app.py` prints nothing.
- `SECURITY.md` has a section on `/w/` and a `/w/` response carries no
  `Access-Control-Allow-Origin` header.
- All server tests pass.

## Scope

`app.py`, `SECURITY.md`, `CHANGELOG.md`, `server/tests/test_routes_new.py`.
