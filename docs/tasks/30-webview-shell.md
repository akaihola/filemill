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
   the Tauri `invoke` bridge. Implement `FS.blob` for native bytes and feed the shared
   `PREVIEW.render` provider; retain object-URL cleanup.
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

## Implementation plan, 2026-09-21

1. Establish automation of the actual application WebView before shell work.
   Use red-green tests and real temporary files. Preserve the UI assertions;
   replace FSA-specific counters with native I/O measurements.
2. Compare minimal Tauri and direct WebKitGTK hosts with one JS port contract.
   Keep the DOM-free model and shared DOM renderer. Package startup assets.
3. Supply native filesystem operations and preview bytes. Keep native history
   with a synchronous JS mirror, including view changes and Back/Forward.
   Isolate untrusted HTML previews from the native bridge.
4. Run the native UI suite on both hosts, measure equivalent release binaries
   and resources, and keep only the smaller passing shell. Record reproducible
   build, run and comparison commands in the README and a native-shell ADR.
5. Run model, bundle, browser, server and pre-commit checks. Update the
   architecture review. Keep every other tracker issue identical to main.

Issue [31] and a native widget renderer are outside this task. Native WebView
automation and availability of WebKitGTK build dependencies are feasibility
gates. A Chromium run with fake handles is not native acceptance.
