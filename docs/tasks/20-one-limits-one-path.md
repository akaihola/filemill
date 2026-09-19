---
depends-on: []
---

# One limits file and one path helper

## Goal

Each shared number and list lives in one file. Roadmap phase 3, step 7.
See `docs/ARCHITECTURE-REVIEW.md`, finding 7.

## Steps

1. Create `ui/core/limits.js`. Export `TEXT_MAX = 512 * 1024` and
   `IMAGE_EXTENSIONS` (one list).
2. Replace `TEXT_MAX` in `ui/adapters/preview-local.js`, `JSONL_MAX` and
   `JSON_MAX` in the JSON adapter, `EDIT_MAX`, and the literal `512 * 1024` in
   `ui/adapters/preview-rich.js` with an import of `TEXT_MAX`.
3. Replace the image lists in `preview-local.js`, `preview-upload.js` and
   `ui/core/render.js` with an import of `IMAGE_EXTENSIONS`. Delete the
   comment in `render.js` that asks a human to keep the lists in step.
4. Create one `mountRoot()` in `ui/core/`. Replace the mount preamble in
   `app-fsa.js` and the two copies in `app-http.js` with a call to it.
5. Keep `currentPath` in `ui/core/deeplink.js`. Delete `pathParts` in
   `ui/core/nav.js`. Change its callers to `currentPath`. Add a test that
   shows the root and an empty leaf give the same result in both callers.

## Done when

- `grep -rn "512 \* 1024" ui/` prints one line, in `limits.js`.
- `grep -rn "pathParts" ui/` prints nothing.
- All static tests and server tests pass.

## Scope

`ui/core/{limits.js,render.js,nav.js,deeplink.js}` and `ui/adapters/`.
