# Native WebView shell

A Linux host that runs the shared DOM renderer in WebKitGTK and supplies the
`FS`, `PREVIEW` and `ROUTER` ports natively. [ADR 0079] records its qualification
through the shared UI scenario, the choice over Tauri and the measured binary
size. These results describe that revision; they are not a fresh qualification
of every later shared UI change.

## Build and run

Linux needs a C compiler, Python 3, pkg-config, GTK 3 and WebKitGTK 4.1
headers and runtime libraries. From the repository root:

```bash
nix-shell native/shell.nix --run 'python3 native/webview/build.py'
native/webview/build/filemill /path/to/folder
```

Without a directory argument, the host opens `FILEMILL_ROOT`, or a native
folder picker when that is unset. The Open Folder button changes the root. The
executable embeds the shared UI, font and icon map. It needs no checkout or
Filemill server at run time, but it still needs its system libraries. A Nix-built binary needs its Nix store
runtime closure on the destination machine.

The 2026-10-17 qualification build used GCC 16.2.0, WebKitGTK 2.54.0, GTK 3.24.52 and glibc
2.44: a 444,520-byte stripped executable with a 334,651-byte embedded UI.

## Port mapping

| Port | Native operation | Shared JavaScript responsibility |
| --- | --- | --- |
| FS | Descriptor-relative list, stat, read and atomic write | Nodes, ordering, errors and Blob conversion |
| PREVIEW | File bytes and metadata through FS | Existing preview renderer table, HTML and object-URL cleanup |
| ROUTER | In-memory history with push, replace and navigation | Synchronous location mirror, view state, callbacks and fullscreen exit |

The native bridge is `webkit.messageHandlers.filemill`. Paths are relative
to the selected root. The host refuses symlinks and parent traversal. HTML
previews are sandboxed; top-level navigation stays on the embedded app.
Reads return bytes and a revision. Writes require that revision and replace
files atomically. A changed or missing revision rejects with `ESTALE`; the editor
keeps the draft. See [ADR 0090] for replacement metadata rules and external-writer
race limits. A failed call rejects with the errno name
first, such as `EACCES: Permission denied`; the text after it follows the
locale.

The host turns off GTK overlay scrolling. WebKitGTK's overlay scrollbars
take clicks across a 21 px band over the rows beneath them; classic
scrollbars take layout space instead.

Native deletion and remembered folders are not implemented. File I/O runs
on the UI thread. Raw-file links and on-demand rich-preview assets are not
verified natively; the UI suite runs with rich previews off.

## Checks

WebKitWebDriver controls the application WebView. Xvfb uses 96 DPI so native
pointer coordinates match CSS pixels. No browser download is needed.

```bash
nix-shell native/shell.nix --run 'uv run --project server pytest native/test_host.py -q'
nix-shell native/shell.nix --run 'uv run --project server pytest static/tests/test_ui.py --native -q'
```

The first command runs 19 contract checks. The second runs the UI sections
that use the shared browser fixture in the native host. The test driver writes the
fixture's bytes into temporary files and exercises the native port; it does
not substitute fake handles for native reads. Where the fake handle counts
`getFile()` calls, the driver counts native `stat` and `read` calls. Delay
injection and fixture mutation live in test support, outside the application.

The driver follows Playwright's rules for clicks and waits. A click waits for
a stable box, and pointer events that reach another element are cancelled
and retried. Predicates are tested for JavaScript truthiness without being
awaited. Automation sessions use an ephemeral web context, so no setting
survives from one launch to the next.

The 2026-10-17 qualification recorded one failure in five runs while waiting
for the fold dial after resizing a 400 KB single-line JSON preview. Shared
preview reuse has since landed in [the preview renderer]; layout changes keep
the preview DOM and pending fill. This documentation review did not remeasure
WebKit wrapping or the native failure rate. Broader async ownership remains
in the [architecture review].

`--native` changes the UI sections that use the shared `browser` fixture.
Tests that create their own browser keep their browser adapters, including
IndexedDB and FSA-specific checks.

[ADR 0079]: ../docs/adr/0079-native-shell.md
[ADR 0090]: ../docs/adr/0090-revision-checked-file-replacement.md
[the preview renderer]: ../ui/core/render.js
[architecture review]: ../docs/ARCHITECTURE-REVIEW.md#a9-broader-preview-and-navigation-async-ownership
