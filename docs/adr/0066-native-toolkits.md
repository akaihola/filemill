# ADR 0066: Keep the shared WebView renderer

Date: 2026-09-21. Issue: [31](../tasks/31-native-toolkit-evaluation.md).

## Context

Filemill needs folding Miller columns, keyboard navigation, structured-file columns and offline previews across editions. Preserve the DOM-free model and three ports. [Evidence and official sources](../tasks/31-native-toolkit-evaluation.md#evaluation-evidence) distinguish capabilities from proposed integration work.

| Option | Columns and folding | Markdown, source and PDF | Build and reuse cost |
| --- | --- | --- | --- |
| Existing WebView | Shared DOM columns and folding; native hit-testing failure remains | Shared HTML renderers and editor; PDF iframe is engine-dependent; native rich assets remain unfinished | Linux C host, GTK 3 and WebKitGTK 4.1; reuses model, renderer and UI scenarios |
| AppKit on macOS | NSBrowser supplies hierarchical columns; custom spines and NSAnimationContext integration still needed | AttributedString Markdown plus NSTextView; highlighting needs token attributes; PDFKit PDFView | macOS SDK and system frameworks; new renderer and native UI tests; JavaScriptCore is a model bridge candidate |
| GTK 4 for GNOME | One virtualized GtkListView per directory; custom fold layout, with GtkRevealer a transition candidate | GtkSourceView 5 for source/editing; Markdown parser and layout needed; Poppler plus viewer controls for PDF | C toolchain and GTK 4 dependencies, distinct from the current GTK 3 WebView host; new renderer, preview libraries and JS bridge |
| WinUI 3 on Windows | Lists or ItemsRepeater per directory; custom folding with XAML animations | RichEditBox for editing; Markdown/highlighting integration needed; Windows.Data.Pdf pages need viewer controls | Windows App SDK and Windows build tools; shared or bundled runtime; new renderer, JS engine bridge and native tests |

Native controls can improve platform integration. They do not establish Filemill keyboard, accessibility or preview parity. All candidates need custom focus/fold tests; HTML preview reuse would retain a WebView and its isolation requirements. GTK has other platform backends, but that does not establish AppKit or WinUI behavior.

## Measurement

[ADR 0065](0065-native-shell-qualification.md) records a stripped Linux host of 395,368 bytes including a 288,599-byte UI input. System GTK/WebKit and the Nix runtime closure are excluded. Earlier Tauri measured 3,053,312 bytes with different inputs and coverage; it is not an equal-input size comparison.
Native toolkit build hours, executable/runtime sizes, memory and latency are unmeasured. No widget prototype was built. AppKit system frameworks, GTK dependencies and Windows App SDK deployment must be counted separately from application bytes.
The recorded host has ten passing native checks and one failing scrolled-row test. The full UI scenario stops there. The existing 1,000/3,000-entry re-render and keystroke targets are each below 100 ms; native performance is not qualified.

## Decision

Keep the shared WebView approach and finish its qualification in later work. Do not start a native widget port. This selects an approach, not a release binary, and does not override ADR 0065.
Reject AppKit now because it adds a macOS-only renderer and preview work. Reject GTK 4 now because accessible folding, preview integration and a JS bridge remain new work despite Linux tool availability. Reject WinUI 3 now because it adds Windows-only tooling, runtime deployment and another renderer. No measured parity or footprint benefit offsets those costs yet.

## Consequences

Keep one UI across browser editions and the prototype. Retain engine dependencies, platform-host work and the known qualification blocker. The hit failure is not proof that GTK native widgets would fix it.
A later port proposal must preserve the model or cost an explicit language port; DOM renderers cannot run in a bare JS engine. It must name a maintainer, target OS/toolchain, preview dependencies and reproducible build commands before implementation.
Reconsider after native UI qualification, or evidence that a required interaction cannot be made reliable in the WebView. A later authorized experiment must compare identical fixtures, folding/focus, structured data, save/history, screen-reader and keyboard behavior, offline previews, root isolation, runtime closure, memory and the existing latency budgets. Keep untrusted HTML away from filesystem bindings.
