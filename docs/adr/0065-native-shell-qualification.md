# Native shell qualification is deferred

Date: 2026-09-21. Issue: [30](../tasks/30-webview-shell.md).

## Context

The DOM renderer needs a native host with filesystem, preview and routing
ports. Compare a direct Linux WebKitGTK host with Tauri 2.11.6.

## Measurement

The direct host's preliminary stripped binary was 399,464 bytes. Tauri's was
3,053,312 bytes. Their embedded UI inputs were 289,624 and 288,920 bytes.
System libraries are excluded. Feature coverage and inputs differed, so
these numbers are not a final equal-input comparison.

Both native UI runs stop at a visible scrolled row whose center hits the
outer `#finder` instead of the row. WebKitGTK 2.52.5 and 2.52.6 reproduce it.
The focused native suite has eight passes and this one failure.

## Decision

Do not select or release a "smallest passing" binary. Keep the direct host as
an unfinished investigation candidate. Remove the temporary Tauri source
from the current tree; its source, lockfile and commands remain in history.
Find that source commit with:

```bash
git log --diff-filter=A --format=%H -- native/tauri/Cargo.lock
```

## Consequences

Fix the focused regression and finish the native UI run before selecting a
shell. Rebuild both candidates with identical UI inputs for the final size
comparison. Raw links and rich assets also need native integration. Issue
[31] remains untouched; no native widget renderer has been evaluated.
