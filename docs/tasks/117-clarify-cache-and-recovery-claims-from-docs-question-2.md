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

## Implementation, 2026-10-20

[ADR 0089](../adr/0089-an-offline-server-shows-older-copies-with-an-indicator.md)
records the decision and the cache policy.

- The server worker, [server/src/filemill/static/sw.js](../../server/src/filemill/static/sw.js),
  is network-first, except for exact content-hashed module URLs. It keeps
  shells marked `X-Filemill-Shell`, UI assets by path and up to 200 reads of
  at most 2 MiB. It answers from a copy, marked
  `X-Filemill-Offline: copy`, only when the server does not answer or a proxy
  answers 502–504. Otherwise it gives a valid 503 marked `miss`, the recovery
  page for a navigation. Activation deletes only `filemill-v1` and older
  `filemill-server-*` caches.
- [ui/adapters/server-status.js](../../ui/adapters/server-status.js) owns the
  top-bar indicator: offline, reconnecting, refused and recovered. Its probe
  fetches the shell with `cache: "no-store"` and takes the new mutation token.
  [ui/adapters/http.js](../../ui/adapters/http.js) sends every request
  through `serverFetch` and marks nodes read from copies `stale`.
- [ui/adapters/app-http.js](../../ui/adapters/app-http.js) remounts the served
  root on recovery when reads were answered offline. Its welcome screen tells
  an unreachable server apart from a root the server cannot open.
- [ui/editor/editor.js](../../ui/editor/editor.js) does not open a stale node,
  so an offline copy cannot be saved over newer bytes.
- The static edition's worker is unchanged. A5 stays open for it.

### Validation, 2026-10-20

- Red first: on the base commit the new browser tests failed with no
  indicator, `Failed to fetch` for offline API reads, an online read returning
  the older `hello` instead of `newer`, and activation deleting another app's
  cache. The shell-marker unit test failed without `X-Filemill-Shell`.
- A high-effort review found that an offline copy of a heading-browsed
  document stayed editable, and that a refusal after offline reads skipped the
  reread. Two tests failed for those before the fixes. The same pass led to
  shell borrowing without `hidden` or `layout` switches, exact-version module
  copies, serialised cache writes and a HEAD heartbeat. A test that routes
  `/api/raw` now uses a page without the worker, because Playwright cannot
  route requests a worker answers.
- Server suite: 1137 passed. `test_documentation_uses_portable_development_examples`
  fails only inside the agent sandbox, which masks `.claude/loop.md`; with the
  sandbox off, `server/tests/test_docs.py` passed 21 of 21.
- Static suites: 160 passed with `--bundle` and 160 with `--dev`.
- After rebasing onto `main` with
  [hiding the ineffective server preview switch](118-hide-the-ineffective-server-preview-switch-from-docs-question-3.md):
  server suite 1139 passed (the docs guard 21 of 21 with the sandbox off) and
  static `--bundle` 160 passed.
- Lint gates: ruff, ruff format, mypy, `deno fmt --check ui/`,
  `deno lint ui/`, the model tests and `static/build-index.py --check` pass.
- One run of the full server suite timed out a Firefox fragment check under
  load; all 14 fragment cases passed on rerun and in the next full run.
- Screenshots at 1280×720 and 390×844 showed the expanded details wrapping
  inside the viewport with the label unclipped.
