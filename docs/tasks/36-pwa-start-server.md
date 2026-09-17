# Start the Filemill server for the installed PWA

The installed PWA uses the server on its own origin. Start it before opening
the app:

```bash
uv run filemill [ROOT]
```

If the server is stopped, the server edition shows `Filemill server
unavailable`, explains that the browser cannot start a native process, shows
the command, and provides `Retry connection`. The service worker keeps the
shell available so this recovery page can render even when API requests fail.

This is the supported recovery flow for every desktop platform. The default
listener is `127.0.0.1:8000`; use `--bind` only when the server must be
reachable from another device.

Systemd and launchd units are rejected for this task because they require
platform-specific installation and lifecycle configuration. A launcher still
requires a separately installed native command and does not let a PWA start
it. A desktop shell would own the process, but is a larger product and
packaging project covered by [30] and [31].

The decision is recorded in [ADR 0063](../adr/0063-installed-pwa-server-recovery.md).

[30]: 30-webview-shell.md
[31]: 31-native-toolkit-evaluation.md
