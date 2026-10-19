# ADR 0079: Keep the direct WebKitGTK shell

Date: 2026-10-17. Issue: [30]. Supersedes [ADR 0065].

Path update, 2026-10-19, issue [109]: `static/test-ui.py` below is now
`static/tests/test_ui.py` (`587752b4`).

## Context

Issue [30] asks for one native shell that runs the shared DOM renderer,
supplies `FS`, `PREVIEW` and `ROUTER` natively, and is the smallest binary
that passes `static/test-ui.py`. ADR 0065 deferred the choice because both
candidates stopped at a visible row whose centre hit `#finder`.

WebKitGTK draws overlay scrollbars that take no layout space but receive
clicks across a 21 px band. That band covered the last visible row of a
column and the chevron end of every row in a scrolling column. The CSS
scrollbar properties did not change it. Turning off GTK's
`gtk-overlay-scrolling` setting gives classic scrollbars, which take layout
space, so rows end where the scrollbar starts.

## Measurement

| Shell | Stripped x86-64 executable | Embedded UI | Executable without UI | `test_ui --native` |
| --- | --- | --- | --- | --- |
| Direct WebKitGTK, `native/webview/` | 444,520 bytes | 334,651 bytes | 109,869 bytes | 220 checks pass in 4 of 5 runs |
| Tauri 2.11.6, removed 2026-09-21 | 3,053,312 bytes | 288,920 bytes | at least 2,764,392 bytes | not rerun |

The direct host was built with GCC 16.2.0 (`-Os -s`) against WebKitGTK
2.54.0, GTK 3.24.52 and glibc 2.44. Both sizes exclude system libraries and
the Nix runtime closure.

Tauri was not rebuilt with the current UI. Its release build downloads the
locked crate graph and runs an LTO build, which this environment's policy
reserves for another machine. The order cannot change. Without any of its
embedded UI, the Tauri executable is still more than six times the direct
host's total size. A Tauri candidate with the direct host's root picker,
navigation policy and atomic writes would add code, not remove it.

## Decision

Keep the direct WebKitGTK host as the native shell. The host turns off GTK
overlay scrolling, and automation sessions use an ephemeral web context so
one test launch cannot inherit another's settings. The Tauri source stays
out of the tree; commit `f73912b4` holds it.

## Consequences

The shell runs on Linux only and needs GTK 3 and WebKitGTK 4.1 at run time.
Its scrollbars are 21 px classic GTK scrollbars, wider than the browser
edition's styled ones, so a scrolling column loses that width to its
scrollbar. Native errors start with the errno name, for example `EACCES:`,
so the adapter does not depend on the locale.

Deletion and remembered folders are not implemented. Raw-file links and
on-demand rich-preview assets are not verified natively; the UI suite runs
with rich previews off. File I/O runs on the UI thread. The other tests in
`static/test-ui.py` keep their browser adapters.

WebKit wraps a long unbroken line, such as minified JSON, about a hundred
times slower than Chromium, and every render rebuilds the preview (finding
A9). With the 400 KB `deep.json` fixture selected, a resize stalls the page
for several seconds. One run in five of the native UI scenario times out
waiting for the fold dial to settle after that resize.

[30]: ../tasks/30-webview-shell.md
[ADR 0065]: 0065-native-shell-qualification.md
