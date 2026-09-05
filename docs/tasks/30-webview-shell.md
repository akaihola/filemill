---
depends-on: [29]
---

# Prototype one native shell

## Goal

One native application runs the DOM renderer in a WebView and supplies the
three ports (`FS`, `PREVIEW`, `ROUTER`) from native code. Roadmap phase 9,
step 2.

## Steps

1. Read `ui/core/ports.js`. It lists every port function and node field.
2. Build the smallest shell with Tauri. Put it in `native/tauri/`.
   The shell serves `static/index.html` from its resources.
3. Implement the `FS` port with native file reads. Expose it to the page with
   the Tauri `invoke` bridge. Implement `PREVIEW.blob` the same way.
   Implement `ROUTER` with an in-memory path.
4. Build the same shell with the platform WebView (WebKitGTK on Linux) in
   `native/webview/`. Use the same JavaScript bridge names.
5. Run `static/test-ui.py` against each shell through its `FS` port.
6. Compare binary sizes. Keep the smaller shell that passes. Delete the other.

## Done when

- One shell in `native/` passes `static/test-ui.py`.
- `README.md` says how to build and run it.
- The binary size is recorded in `docs/adr/NNNN-native-shell.md`.

## Scope

`native/`, `ui/core/ports.js`, `docs/adr/`, `README.md`.
