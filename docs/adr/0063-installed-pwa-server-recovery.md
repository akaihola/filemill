# Installed PWA server recovery

Date: 2026-09-17

## Status update, 2026-10-19, issue [109]

The shell's recovery page shows `uv run filemill`, without `[ROOT]`
(`showServerUnavailable` in `ui/adapters/app-http.js`). Since `87bc1f5d`
(2026-09-21), the server's service worker also answers a navigation that the
server does not answer with its own recovery page, whose retry reloads the
page (`server/src/filemill/static/sw.js`). Finding A5 of the
[architecture review](../ARCHITECTURE-REVIEW.md) tracks the remaining caching
problems.

## Context

An installed PWA can open its web origin, but browser sandbox rules do not let
it start a local Filemill process. Opening the app while the server is stopped
must give users a supported next action.

## Decision

Use a server-not-running recovery page. The server edition keeps its shell and
service worker available, detects a failed root mount, and displays the
`uv run filemill [ROOT]` command plus a retry button. The retry remounts the
server without requiring an app reinstall. The default server bind remains
loopback (`127.0.0.1`), which is the platform scope for this flow.

## Rejected alternatives

- systemd or launchd units: useful for power users, but require a separate
  platform-specific installation and are outside the PWA package.
- launcher: can start Filemill and open a browser, but still requires a native
  launcher and does not make the installed PWA self-starting.
- desktop shell: can own the server process, but requires a new packaged
  application and native integration; see [30] and [31].

## Consequences

The PWA remains a browser client and works on desktop platforms supported by
the browser. Users start the server through their platform shell. The page
provides a clear recovery path, but it does not provide background startup.

[30]: ../tasks/30-webview-shell.md
[31]: ../tasks/31-native-toolkit-evaluation.md

[109]: ../tasks/109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md
