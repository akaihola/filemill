---
depends-on: [30]
---

# Evaluate fully native toolkits

## Goal and scope

Compare AppKit, GTK and WinUI with the existing WebView prototype. Record
an evidence-backed recommendation in an ADR before any native toolkit work.
This task changes documentation only. The task brief of 2026-09-21 replaces
the earlier instruction to build and time a throwaway native column.

## Plan

1. Move only the unchanged [31] block to In Progress and commit this setup.
2. Compare columns, folding, previews, editing, accessibility, model reuse,
   performance, security, runtime dependencies and build costs. Use repository
   evidence and official toolkit documentation. Label unmeasured quantities.
3. Write an ADR under 40 lines with the comparison, recommendation, rejected
   options and gates for later work. Link it from the architecture review.
4. Run all pre-commit hooks, verify links and the complete diff against main.
   Removing [31] from each tracker must leave byte-identical remaining text.

## Baseline constraint

The brief calls [30] complete. The repository still records it as In Progress
with an unqualified WebKitGTK host. Use that result without claiming native
UI parity or changing [30]. See [ADR 0065](../adr/0065-native-shell-qualification.md).
Do not implement a toolkit or repair the prototype in this task.

## Evaluation evidence

Decision: [ADR 0066](../adr/0066-native-toolkits.md). Official sources below
were checked on 2026-09-21. API capabilities are documented facts. Candidate
combinations and their Filemill costs are engineering judgments, not tested ports.

### Repository baseline

- [Native build](../../native/webview/build.py) embeds the UI with `cc -Os -s`
  and `webkit2gtk-4.1`. [The shell](../../native/shell.nix) supplies GTK 3,
  WebKitGTK, Python and a C compiler. This is a WebView inside GTK, not a
  native-widget rendering of Filemill. Only Linux has a retained host.
- [NativeFS, NativePreview and NativeRouter](../../ui/adapters/native.js)
  bridge filesystem operations and history. Preview rendering still delegates
  to JavaScript. [Startup](../../ui/adapters/app-native.js) registers shared
  renderers and JSON/CSV virtual-file adapters.
- [Folding arithmetic](../../ui/core/model/folding.js) has no DOM dependency.
  [The renderer table](../../ui/core/renderers.js) returns HTML and uses Blob
  URLs and iframes. A JavaScript engine alone cannot display those previews.
  Reuse of ES modules also needs a loader, host values and callback bindings;
  an engine's ability to evaluate JavaScript is not a ready-made adapter.
- [Native limitations](../../native/README.md) include UI-thread file I/O,
  unfinished raw links/rich assets and no native deletion. PDF iframe support
  must be verified in the actual engine; its presence in code is not proof.
- [The UI test](../../static/test-ui.py) checks viewport-sized row counts and
  re-render/keystroke costs below 100 ms for 1,000 and 3,000 entries. These are
  regression ceilings, not measured native results. Preserve the folding
  and focus rules in [ADR 0062](../adr/0062-narrow-screen-layout-model.md).
- [The host](../../native/webview/main.c) walks paths relative to a root
  descriptor, refuses parent traversal and symlinks, and saves atomically.
  HTML iframes have an empty sandbox; top-level navigation is restricted.
  Every replacement must retain these boundaries and test malicious previews.

### AppKit

[NSBrowser](https://developer.apple.com/documentation/appkit/nsbrowser)
provides hierarchical columns. Filemill's persistent folded spines and focus
protection still need custom integration. [NSAnimationContext](https://developer.apple.com/documentation/appkit/nsanimationcontext)
is an animation mechanism, not that folding policy.
[AttributedString Markdown](https://developer.apple.com/documentation/foundation/instantiating-attributed-strings-with-markdown-syntax)
and [NSTextView](https://developer.apple.com/documentation/appkit/nstextview)
are text candidates; preserving tables, fenced-code highlighting and link
rules needs explicit work. [PDFView](https://developer.apple.com/documentation/pdfkit/pdfview)
provides PDF display, navigation and selection.
[JavaScriptCore](https://developer.apple.com/documentation/javascriptcore)
can host JavaScript and native bindings. It does not supply the DOM renderer.
[AppKit accessibility](https://developer.apple.com/documentation/appkit/accessibility-for-appkit)
helps standard controls; custom spines need accessibility roles and testing.
This is a macOS renderer using the macOS SDK and system frameworks. It would
need Mac build/release validation and native UI automation alongside browser
coverage. No Mac build, distribution size or implementation hours were measured.

### GTK 4

[GtkListView](https://docs.gtk.org/gtk4/class.ListView.html) creates visible
rows from a model and exposes list accessibility roles. Use one list per
folder, not a table's columns as directory levels.
[GtkRevealer](https://docs.gtk.org/gtk4/class.Revealer.html) supplies transitions,
but its hidden child remains in the accessibility tree. Filemill needs a
custom spine/focus policy, not a direct hide/show substitution.
[GtkSourceView 5](https://gnome.pages.gitlab.gnome.org/gtksourceview/gtksourceview5/)
provides source editing and language highlighting. Rendered Markdown still
needs parsing and widget layout, or an explicitly hybrid WebView.
[Poppler](https://poppler.freedesktop.org/) is a PDF rendering library;
viewer controls and dependency/license review remain integration work.
[GTK 4 build documentation](https://docs.gtk.org/gtk4/building.html) describes
Linux, Windows and macOS backends. GTK 4 plus preview libraries and a JS engine
adds a different dependency set from the GTK 3 host. It is the most accessible
candidate on this Linux machine, but no runtime size or latency advantage has
been measured. GNOME keyboard/screen-reader tests and platform packages would
be new maintenance work; other backends do not prove native desktop parity.

### WinUI 3

[ItemsRepeater](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/items-repeater)
supports custom virtualized layouts, but selection and interaction policy
need application code. Lists per folder and [XAML animations](https://learn.microsoft.com/en-us/windows/apps/develop/motion/storyboarded-animations)
are candidates for custom folding. Focus, selection and accessible hierarchy
must be tested with the Filemill keyboard rules.
[RichEditBox](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/rich-edit-box)
edits rich text; Filemill must add Markdown rendering and source highlighting.
[Windows.Data.Pdf](https://learn.microsoft.com/en-us/uwp/api/windows.data.pdf.pdfdocument)
loads PDF documents; page rendering needs a viewer UI and does not establish
text-selection parity with PDFView. A WebView preview would keep web dependencies.
[WinUI project setup](https://learn.microsoft.com/en-us/windows/apps/winui/winui3/create-your-first-winui3-app)
requires a Windows development environment and Windows App SDK tooling.
[Deployment](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/deployment-architecture)
can share the framework runtime or bundle it. A C# choice also affects .NET
runtime costs. A JS engine and model bridge are additional choices, not WinUI
features. Windows UI automation and deployment checks would be new work.
No Windows build, runtime footprint or implementation hours were measured.

### Recommendation and later evidence

Retain the WebView renderer because it preserves the implemented UI and its
browser coverage. This is a maintenance judgment, not a speed/size victory.
AppKit offers the closest ready-made columns and PDF viewer; GTK offers the
closest local build environment; WinUI offers Windows integration. None has
shown Filemill parity or enough benefit to fund a separate renderer now.
All require an explicit offline preview strategy for Markdown, PDF, HTML and
office files, with plain fallback and no unsolicited network access. Preserve
JSON/CSV virtual columns and assess SQLite/server gaps against the same fixtures.

A later implementation task must name its platform, owner and dependencies,
keep DOM-free model tests, and add native interaction tests for the existing
UI scenarios. Measure equivalent release inputs on named OS/toolchain versions.
Report executable, bundled assets and installed runtime closure separately;
also measure memory, latency and engineering hours. This task authorizes no
such build and makes no change to the unfinished [30] qualification work.

## Validation, 2026-09-21

- The comparison ADR was absent before this task. ADR 0066 now has 33 lines,
  all four options and the required decision sections. Relative links resolve.
  Official capability sources were read; Apple API text was also available
  through indexed official documentation when its Markdown endpoint failed.
- `pre-commit run --all-files`: five hooks passed, one inherited failure.
  Ruff lint, mypy, Deno format/lint and bundle consistency passed.
  `ruff-format` would join two adjacent strings at
  `server/tests/test_browser_new_ui.py:1831`. Its working-file Git blob equals
  `main`'s blob, `cdd269793debb6340516a692892d9c5ed0450b73`.
  No source formatting change was made for this documentation task.
- The shell did not expose `pre-commit`. A temporary `uv tool run` attempt
  could not reach PyPI. The installed package ran successfully via
  `python3 -m pre_commit run --all-files`, with its site-packages on
  `PYTHONPATH` and `PRE_COMMIT_HOME` under `/tmp`. The hook failure above is
  the actual validation result, not a missing-tool result.
- `git diff --check` and `git diff main --check` passed. A byte comparison
  removed the unchanged [31] block and separator from both trackers; all
  remaining bytes matched. [31] occurs once under In Progress. Completion
  movement belongs to the later merge workflow.
- The change contains only this task document, ADR 0066, the architecture
  update and the [31] tracker move. No native toolkit was built or started.
  Historical native results were not rerun or claimed as fresh measurements.
