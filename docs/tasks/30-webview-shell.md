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

### Final rebased checks

Rebased onto `main` at `01836d3`. The tracker conflict was resolved from
main's complete text, then only the unchanged [30] block was moved. Removing
that block from both files leaves byte-identical text.

All six pre-commit hooks, the model checks and bundle consistency check pass
on the rebased tree. The three incoming server preview-delete tests and the
static context-menu deletion test pass. The rebuilt native host still has
eight passing contract tests and the one scrolled-row failure. Those tests
launch the embedded executable with a temporary working directory outside
the checkout. The retained build is 395,368 bytes with a 288,599-byte UI input.

### AI implementation review, 2026-09-21

The initial tracker/documentation commit precedes implementation. The saved
plan still cannot be accepted as implemented: the full native UI scenario
fails, later interactions and raw/rich integration remain unfinished, and
neither candidate qualifies for the required binary comparison.

Review added failing real-WebView regressions and repaired two defects:

- Native writes truncated text at an embedded NUL. JSC byte-string conversion
  and an explicit byte count now preserve the complete UTF-8 contents.
- The UI driver registered console listeners without forwarding errors.
  It now delivers console errors once, so the UI suite can detect them.

The rebuilt native suite reports **10 passed, 1 failed**. The sole failure
is still `test_scrolled_row_remains_clickable`. The native `test_ui` scenario
also fails at the same covered row after these repairs. Review independently
reproduced the geometry and tried removing custom scrollbar rules, explicit
scrollbar dimensions, default scrollbar colors/widths, vertical `clip`, extra
bottom padding and always-visible scrollbars. None repaired the hit result.
These probes were temporary; no speculative renderer CSS was retained. This
confirms a reproducible qualification blocker, not a proven upstream cause.
The retained executable is still 395,368 bytes; embedded UI is 288,599 bytes.

Model tests, bundle consistency, all six pre-commit hooks and native Python
lint/format checks pass. `uv run --project server pytest static/test-ui.py -q`
passes all seven browser tests in 134.74 seconds. The earlier full repository
and modular-static results remain the implementation baseline; this review
changed only native code, native test support and documentation.

Tracker proof against `main` at `01836d3`: removing the exact unchanged [30]
block from both versions leaves byte-identical text. All 52 numbered issues
occur exactly once; all 122 issue blocks, including unnumbered proposals,
are unique across headings. [30] occurs only under In Progress. [31] remains
unchanged. No task completion or binary selection is claimed.

### Merge and deployment, 2026-09-21

Merged the reviewed prototype with `--no-ff` as `72e16aa`. Both worktrees
were clean after the merge. This preserves the unfinished prototype and its
blocker evidence; [30] remains In Progress because no native binary passes
the complete UI suite. No completion move is warranted. [31] is unchanged.

Restarted the development service and the public service, both running from
main's development tree. Both are active. The merged entry module,
`core/nav.js` and `core/renderers.js` match byte for byte on the development and public listeners and through `https://filemill.vempai.men/`. Live Chromium checks pass
on all three origins for keyboard navigation with no welcome element and
HTML preview content whose script cannot access its parent. These checks
used in-memory preview content and did not modify served files.

The native prototype is a local build, not a public native release. Updating
the web services deploys the shared keyboard and HTML preview fixes. The
web application does not gain the native bridge.

### Try the changes

1. For the prototype, follow [build and run](../../native/README.md#build-and-run)
   against a disposable folder. Open a text file, browse with the arrow keys,
   and try Back/Forward. The [port mapping](../../native/README.md#port-mapping)
   explains which work occurs natively. Use the [checks](../../native/README.md#checks)
   to reproduce the known narrow-window click failure; this is not a qualified
   replacement for the browser edition.
2. On the [public finder](https://filemill.vempai.men/?filemill=render), refresh
   and use Down/Up to move selection. The server edition has no welcome screen;
   keyboard navigation must still work.
3. In a disposable local folder, create `preview.html` containing a heading and
   `<script>document.body.textContent='SCRIPT RAN'</script>`. Open its HTML
   preview in the native prototype or static edition. The heading should remain
   visible; the script must not replace it. This concerns the embedded preview,
   not deliberately opening a raw HTML document as a separate page.
4. To verify the write and test-reporting repairs without altering personal
   files, run from the repository root after building the prototype:

   ```bash
   nix-shell native/shell.nix --run 'uv run --project server pytest native/test_host.py -k "embedded_nul or reports_console" -q'
   ```

   These two checks exercise the real WebView. They verify that an embedded
   NUL does not truncate a save and that console errors reach the UI test
   assertions. Both pass; they do not replace the still-failing full native
   qualification suite.

## Qualification, 2026-10-17

The direct WebKitGTK host passes `static/test-ui.py::test_ui --native`. All
220 checks passed in four of five consecutive runs. The fifth hit the known
WebKit layout stall described below. [ADR 0079] keeps this shell, records its
size and supersedes [ADR 0065]. The tracker issue moves to Completed /
Accepted with `[ ]`, pending user acceptance.

### Cause of the blocker

WebKitGTK 2.54.0 reproduced the scrolled-row failure. `#finder` scrolls
horizontally, yet its client and offset heights were both 260 px, so its
scrollbar was an overlay. Every point in its bottom 21 px hit `#finder`. A
new check found the same band at the right edge of a scrolling column, where
a row's chevron end hit `.col-body`.

`scrollbar-width`, `scrollbar-color`, `scrollbar-gutter`, `overflow-x:
scroll` and `::-webkit-scrollbar` did not change the band, and
`GTK_OVERLAY_SCROLLING=0` had no effect. Setting GTK's
`gtk-overlay-scrolling` to false in the host gives classic scrollbars.
`#finder`'s client height drops to 239 px, and rows end above the scrollbar.

### Further fixes, each with a failing check first

- Native errors begin with the errno name. Under a Finnish locale, a locked
  folder showed `Error: Lupa evätty` instead of "No permission to read".
- Automation sessions use an ephemeral web context. Earlier test runs left
  a size sort in `~/.local/share/filemill`, and later launches started with
  it. That directory is the native app's real profile; it was not deleted.
- `native/shell.nix` exposes libstdc++, which Playwright's greenlet wheel
  needs before `static/test-ui.py` can import.
- The UI driver follows Playwright's rules. `wait_for_function` takes `arg`
  and tests JavaScript truthiness without awaiting a returned promise. A
  click waits for a stable box; when the press or the click reaches another
  element, both are cancelled and the click is retried. Read counts come
  from native `stat` and `read` calls at the bridge, because the port
  wrappers copy `loadMeta` at startup. The driver also gained
  `Locator.press`, removes fixture folders and keeps a simulated slow read
  marked as loading.

The click rule matters at 390 px. When `level-3` opens, column 5 starts at
x=391 in both Chromium and WebKit, so the next row is off screen. Both
drivers scroll it into view, and the app returns `#stage` to 0 on its next
scroll event. In WebKit that reset can arrive between press and release,
sending the click to `#strip`.

### Deep JSON stalled JavaScriptCore

After those fixes, the full native scenario still failed about two runs in
five while waiting for the fold dial to settle. Timing every WebDriver call
showed 2–4 s stalls while `mixed/deep.json` was selected. Inside the page,
`setTimeout(0)` fired after 2,898 ms. The fixture nests 200,000 arrays.
JSON was shown as source only after recursion exhausted the stack, and
JavaScriptCore recursed for seconds first. `JSON.stringify` alone took
2.5 s before failing, and the preview rebuilt on every render. A 1,001-deep
check failed first in Chromium. [ADR 0080] adds a fold depth limit, and the
same render now takes 46 ms in WebKit and 48 ms in Chromium.

### Remaining intermittent failure

After the JSON fix, four of five consecutive native runs passed all 220
checks. The fifth timed out in `scroll_settled` after the resize back to
1500 by 900, with `deep.json` selected again. Re-wrapping its 400 KB
single-line source at a new width takes WebKit 1.4–2.8 s against 10–17 ms in
Chromium, and `render()` builds a new preview element and reads the file
twice (finding A9), so a resize pays the cost twice. `overflow-wrap:
anywhere` and `overflow-wrap: break-word` were no faster. `word-break:
break-all` was fast but splits words anywhere, so no CSS change was kept. The
fix belongs to A9's preview reuse, not to this issue.

### Size comparison

The direct host is a 444,520-byte stripped executable with a 334,651-byte
embedded UI. Tauri 2.11.6 measured 3,053,312 bytes with a 288,920-byte UI on
2026-09-21. Tauri was not rebuilt. Its locked crate download and LTO release
build count as heavy work, which this environment runs on another machine.
Without any of its embedded UI, Tauri is still more than six times the
direct host's total size, so an equal-input rebuild cannot change the order.

[ADR 0065]: ../adr/0065-native-shell-qualification.md
[ADR 0079]: ../adr/0079-native-shell.md
[ADR 0080]: ../adr/0080-json-past-a-fold-depth-limit-is-source.md
