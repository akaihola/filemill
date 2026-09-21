---
depends-on: [36]
---

# Show recovery when the installed PWA starts offline

## Goal

Opening the installed PWA while its Filemill server is stopped shows a useful
recovery page instead of a blank white window. The page names the command to
start and the action to retry the connection.

## Evidence

When the server stops after the PWA is already open, the browser shows a fetch
error. When the PWA is opened after the server is stopped, end-user testing
shows a blank window. The existing server-side recovery markup is therefore
not reached in this startup path.

## Steps

1. Reproduce with a fresh installed PWA and with an already cached service
   worker. Record whether the failure is in the document request, service
   worker fallback, or JavaScript boot.
2. Trace the startup request through the manifest, service worker, shell, and
   `mountServer()` failure path. Preserve network-only behavior for `/api/`.
3. Add a startup fallback that renders the recovery message when the server
   cannot supply the shell. Keep the fallback same-origin and independent of
   the filesystem API.
4. Add a focused browser or static check for opening the PWA with the server
   stopped, including the visible command and retry action.
5. Test the running-server path and the stopped-server retry path.

## Done when

- A fresh or previously installed PWA shows the recovery page when the server
  is stopped before launch.
- Starting `uv run filemill [ROOT]` and choosing Retry reaches the file view.
- API responses are not cached as a substitute for a running server.
- Focused checks pass.

## Scope

`server/src/filemill/static/sw.js`, the server PWA shell and relevant static
UI, `server/tests/test_pwa.py` or browser tests, and this task documentation.
