# Native WebView prototype

Issue [30] is blocked on a WebKitGTK hit-testing failure. This prototype is
not a qualified release. The native contracts pass, but `static/test-ui.py`
does not finish through the native host. See the [issue evidence](../docs/tasks/30-webview-shell.md).

## Build and run

Linux needs a C compiler, Python 3, pkg-config, GTK 3 and WebKitGTK 4.1
headers and runtime libraries. The measured build uses WebKitGTK 2.52.6.
From the repository root:

```bash
nix-shell native/shell.nix --run 'python3 native/webview/build.py'
native/webview/build/filemill /path/to/folder
```

Without a directory argument, the host opens a native folder picker. The
Open Folder button changes the root. The executable embeds the shared UI,
font and icon map. It needs no checkout or Filemill server at run time, but
it still needs its system libraries. A Nix-built binary needs its Nix store
runtime closure on the destination machine.

The measured Nix package revision is
`62c8382960464ceb98ea593cb8321a2cf8f9e3e5`. To use that revision, pass
`-I nixpkgs=https://github.com/NixOS/nixpkgs/archive/62c8382960464ceb98ea593cb8321a2cf8f9e3e5.tar.gz`
to `nix-shell`.

## Port mapping

| Port | Native operation | Shared JavaScript responsibility |
| --- | --- | --- |
| FS | Descriptor-relative list, stat, read and atomic write | Nodes, ordering, errors and Blob conversion |
| PREVIEW | File bytes and metadata through FS | Existing preview renderer table, HTML and object-URL cleanup |
| ROUTER | In-memory history with push, replace and navigation | Synchronous location mirror, view state, callbacks and fullscreen exit |

The native bridge is `webkit.messageHandlers.filemill`. Paths are relative
to the selected root. The host refuses symlinks and parent traversal. HTML
previews are sandboxed; top-level navigation stays on the embedded app.
Writes replace files atomically. Native deletion and persistent recent-folder
storage are not implemented. File I/O runs on the UI thread in this prototype.
Raw-file links and on-demand rich-preview assets still need native integration;
only the embedded core preview path has been qualified by the focused checks.

## Checks

WebKitWebDriver controls the application WebView. Xvfb uses 96 DPI so native
pointer coordinates match CSS pixels. No browser download is needed.

```bash
nix-shell native/shell.nix --run 'uv run --project server pytest native/test_host.py -q'
nix-shell native/shell.nix --run 'uv run --project server pytest static/test-ui.py::test_ui --native -q'
```

The first command currently has eight passing checks and one failing
scrolled-row regression. The second stops on the same interaction. The test
driver writes the existing fixture bytes into temporary files, then exercises
the native port. It does not substitute fake handles for native reads.
Metadata instrumentation counts native stat calls. Delay injection and
fixture mutation live in test support, outside the application.

`--native` changes the main `test_ui` scenario. The other tests in
`static/test-ui.py` retain their browser adapters, including IndexedDB and
FSA-specific checks. Later parts of the native UI scenario remain unverified
until the blocking interaction is fixed.
