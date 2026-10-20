# Show an expandable server-offline indicator with cached content

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md?f), question 2.
User review, 2026-10-20. Label: `steward`.

## Decision

Approved: older content may stay visible while the server is unavailable, provided a clear on-screen indicator says that the server is offline. Tapping or clicking it expands details and recovery instructions. This replaces the earlier docs-only recommendation; removing /w/ is tracked in [129](129-remove-the-obsolete-w-and-n-url-routes.md?f).

## Work

1. First reproduce server loss with a populated view and an installed app. Add failing browser tests for a persistent, readable offline indicator that expands by click, touch and keyboard to show the explanation and retry/start instructions.

2. Determine availability from network requests to the Filemill server, not only the browser's internet-connectivity flag. Distinguish unavailable server, reconnecting, permission failures and successful recovery.

3. Allow previously obtained content to remain visible or be reused offline with the indicator. Online reads must not silently present an older cached version as current. Failed mutations must not appear successful; this does not add offline writes or an edit queue.

4. Define the minimum cache policy needed for the offline read behavior. Preserve unrelated caches, remove obsolete Filemill entries safely and return a valid response when no cached content exists. Cover warm startup and a genuinely uncached destination without promising recovery on a first visit without a worker.

5. In the implementation change, update the A5 acceptance/remediation text in [docs/ARCHITECTURE-REVIEW.md](../ARCHITECTURE-REVIEW.md?f), [ADR 0063](../adr/0063-installed-pwa-server-recovery.md?f), [server/README.md](../../server/README.md?f) and [SECURITY.md](../../SECURITY.md?f). The user's offline-read decision supersedes the old blanket prohibition on cached document bytes; other A5 defects remain.

## Acceptance

Older content is visibly identified while the server is offline; details and instructions are accessible without truncated status text. Recovery refreshes availability and affected content. Tests cover stop/restart, cached/uncached views and unrelated-cache preservation. A5 closes only when its remaining defects are fixed.
