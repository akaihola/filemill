---
depends-on: [32]
---

# Decide the fate of the /w/ named mounts

## Goal

The `/w/<mount>/...` route and its CORS middleware in `app.py` either have a
documented consumer or are gone. Roadmap phase 6, step 4.

## Background

`/w/` serves files under the root and under each symlink child of the root,
with CORS headers for any origin. `rendering.py` used it for Markdown links
to files outside the root. Task [32] deletes `rendering.py`. The CORS scope
suggests an outside consumer, for example the dashboard that embeds
documents. Nothing in `ui/` uses `/w/`.

## Steps

1. Run `git grep -n "/w/" -- ui server/src docs README.md`. List the hits.
2. Ask the repository owner in the pull request whether any outside page
   loads `/w/` URLs. Do not guess.
3. If nobody uses it: delete `web_static`, `_mount_targets`,
   `_resolve_web_mount`, `_mounted_path_parts`, `_web_url`,
   `_WebStaticCORSMiddleware` and `_CORS_HEADERS` in `app.py`, and their tests.
4. If someone uses it: add a `--cors-origin` option to `cli.py`. Without it,
   the middleware sends no CORS headers. Write the threat and the option in
   `SECURITY.md`.

## Done when

- Either `grep -n "/w/" server/src/filemill/app.py` prints nothing, or
  `SECURITY.md` has a section on `/w/` and the default sends no CORS header.
- All server tests pass.

## Scope

`app.py`, `cli.py`, `SECURITY.md`, `server/tests/`.
