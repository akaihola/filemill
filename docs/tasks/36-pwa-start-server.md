# Start the Filemill server for the installed PWA

## Problem

The installed PWA opens `http://localhost:8334/`. Nothing starts the server. If
the user did not run `filemill` in a terminal, the PWA shows a connection error.
A PWA is a browser sandbox. It cannot start a local process.

## Options

1. **System service.** Ship a `filemill.service` unit for systemd (Linux) or a
   launchd plist (macOS) that starts the server at login. The user must install
   it one time outside the browser.
2. **Launcher.** Ship a `.desktop` file (Linux) or an `.app` wrapper (macOS)
   with `Exec=filemill --open`. It starts the server and opens the browser. One
   click, but the PWA still does not start the server by itself.
3. **Desktop shell.** Bundle the server in an Electron or Tauri app that owns
   the process. Full native feel, heavy packaging. See [30] and [31].
4. **Better failure.** Make `sw.js` cache the shell and show "server not
   running, start it with `filemill`" instead of the browser error. Does not
   solve the problem. Improves the failure mode.

## Done when

- One option, or a combination, is chosen and recorded as an ADR in
  `docs/adr/`.
- A follow-up bullet for the chosen implementation is in `TASKS.md`.

[30]: 30-webview-shell.md
[31]: 31-native-toolkit-evaluation.md
