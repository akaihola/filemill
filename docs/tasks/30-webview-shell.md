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

## Implementation evidence, 2026-09-21

Status: blocked on native UI qualification. Keep [30] In Progress. No passing
winner has been selected, and issue [31] has not been started.

The WebKitGTK host embeds the shared renderer and exposes native filesystem
operations and history. Preview bytes come from the native filesystem; the
existing JS renderer table produces DOM content. Build, run and port details
are in [native/README.md](../../native/README.md).

Red-green checks exposed and fixed a shared directory-descriptor offset on
refresh, missing keyboard handling when no welcome element exists, unsafe
HTML preview access, untrusted top-level navigation, and Back behavior while
fullscreen. Eight native checks pass. The ninth intentionally remains red
and reproduces the acceptance blocker.

### Blocking result

At a 568 by 320 viewport, scroll the root list to `wide`. Its visible row has
bounds x=14, y=265, width=134, height=21. The center point is inside the row,
but `document.elementFromPoint()` returns `#finder`. WebDriver rejects the
click. The screenshot shows the row, so treating this as a hidden fixture or
substituting `element.click()` would hide the failure.

Reproduce the focused failure:

```bash
nix-shell native/shell.nix --run 'python3 native/webview/build.py'
nix-shell native/shell.nix --run 'uv run --project server pytest native/test_host.py::test_scrolled_row_remains_clickable -q'
```

The main native UI scenario also stops when it opens `wide` after resizing
to landscape. The same interaction blocks both the direct host and Tauri.
A 96-DPI Xvfb display fixed a separate WebDriver coordinate-scaling problem;
it did not fix this scrolled-row failure.

Safe alternatives tested without retaining speculative CSS changes:

- WebKitGTK 2.52.6 and the installed 2.52.5 runtime reproduce the hit failure.
- Software compositing and `GTK_OVERLAY_SCROLLING=0` do not fix it.
- Removing content visibility, the bottom fade, transforms, sticky positioning,
  or changing positioning, containment and scrollbar gutter does not fix it.
- `overflow:visible` or `scrollbar-width:none` on `#finder` makes the point hit
  the row, but removes clipping or the horizontal scrollbar. These changes
  were not retained because they remove existing UI behavior.
- The installed 2.46.6 driver first failed with incompatible system-library
  resolution. Isolating its library path then timed out during session setup.
  It did not establish an alternative passing runtime.

The remaining native UI assertions, including the large-directory budgets,
have not been qualified. Resume with this focused regression, then run the
complete native UI scenario before choosing a binary.

### Measurements and checks

The direct host measured 399,464 bytes after native picker and history fixes,
with a 289,624-byte embedded UI input. The initial Tauri 2.11.6 release build
measured 3,053,312 bytes with a 288,920-byte UI input. Both are stripped x86-64
Linux executables. These are preliminary measurements with different feature
coverage and UI revisions, not a final equal-input comparison. System GTK and
WebKit libraries are excluded from both executable sizes.

- `node ui/core/model/test.mjs`: passed.
- `python3 static/build-index.py --check`: passed.
- `uv run --project server pytest`: 784 passed, two warnings.
- Native contract suite: eight passed, one failed at the scrolled-row check.
- `static/test-ui.py::test_ui --native`: stopped at the same interaction.
- Tauri real-file filesystem contract: passed; its native UI run also stopped
  at the scrolled-row interaction.

The original pre-commit run passed five hooks and found one native JS format
change. That file was formatted; final hook and rebase results follow below.

The modular static suite passed: `uv run --project server pytest static --dev`
reported 50 passed and one warning. The final pre-commit run passed all six
hooks. Native Python lint and formatting checks also passed.

Raw-file links, on-demand rich assets, and the portions of the native UI suite
after the blocking click still need integration or verification. The direct
host is retained as an unfinished prototype, not as a selected passing binary.

The [qualification ADR](../adr/0065-native-shell-qualification.md) defers the
binary choice. Only the unfinished direct host remains in the current tree.
The temporary Tauri source and locked comparison build remain recoverable
from the commit that added `native/tauri/Cargo.lock`.
