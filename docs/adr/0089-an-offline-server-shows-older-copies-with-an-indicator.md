# 89. An offline server shows older copies with an indicator

Date: 2026-10-20

Status: Accepted

## Context

The server edition's service worker answered every same-origin GET outside
`/api/` from its cache first, so a file read after a save could be the older
copy. It sent navigations to the network, with an inline recovery page when
the server did not answer. An offline miss resolved to `null`, and activation
deleted every other cache on the origin. Finding A5 of the
[architecture review](../ARCHITECTURE-REVIEW.md) records these defects.

When the server stopped under an open page, the page kept showing what it had
read and said nothing about it. A folder opened afterwards said only "Failed
to fetch". Opening the installed app with the server stopped showed the
recovery page and none of the content read before.

On 2026-10-20 the user approved older content staying visible while the
server is unavailable, provided a clear indicator says that the server is
offline, and tapping or clicking it expands details and recovery instructions
([117](../tasks/117-clarify-cache-and-recovery-claims-from-docs-question-2.md)).
That supersedes A5's old acceptance that viewing a file adds no document bytes
to Cache Storage.

## Decision

The server worker (`server/src/filemill/static/sw.js`) is network-first for
every request it handles. Whatever the server answers is what the page gets,
so an online read is never an older copy. A complete answer, status 200 with a
`Content-Length` of at most 2 MiB, is also kept as an offline copy. Only when
the server cannot be reached, or a proxy in front of it answers 502, 503 or
504, does the worker answer from a copy, marked `X-Filemill-Offline: copy`.
With no copy it answers a valid 503 marked `X-Filemill-Offline: miss`: the
recovery page for a navigation, plain text for anything else.

| Cache | Holds | Bound |
| --- | --- | --- |
| `filemill-server-shell-v2` | Shell pages, per address that answered with one | 50 entries |
| `filemill-server-assets-v2` | `/ui/`, the manifest and the icons, per path | One per file |
| `filemill-server-reads-v2` | Listings, file bytes and previews, per URL | 200 entries |

- The shell sends `X-Filemill-Shell: 1`. The worker keeps a navigation only
  with that header, so a user's HTML page or a file's bytes never become an
  offline page without the indicator.
- An address the client writes, with `?filemill=render` or `highlight`, gets
  another address's shell when its own was never loaded, preferably one with
  the same query. A bare address may name file bytes or a user's
  `index.html`, so it gets only its own copy or the recovery page.
- Assets are kept per path, without the `?v=` query, so a shell finds the
  newest copy of each module.
- The worker leaves the network to requests other than GET, other origins,
  `/api/search`, `/sse/`, Range requests and requests made with
  `cache: "no-store"`. Copies ignore `Cache-Control`, because they are only
  ever shown with the indicator.
- Activation deletes `filemill-v1` and `filemill-server-*` caches that are not
  current. Other caches on the origin and IndexedDB stay untouched. The worker
  precaches nothing, so `/` can no longer capture a user's `index.html`.

The page (`ui/adapters/server-status.js`) learns availability from its own
requests to the server. Every request in `ui/adapters/http.js` goes through
`serverFetch`. `navigator.onLine` only prompts a check: headless Chromium in a
sandbox reports `false` while a loopback server answers.

| State | Cause | Indicator |
| --- | --- | --- |
| online | Answers from the server | Hidden |
| offline | No answer, a 502–504, or an offline copy | "Server offline" |
| reconnecting | A probe is waiting | "Reconnecting…" |
| refused | A 403 for a change | "Change refused" |
| recovered | An answer after being offline | "Server back online", for 4 s |

The indicator sits in the top bar. Click, tap, Enter or Space expands it into
an explanation, the start command and a Retry now button. Escape closes it.
The details wrap within the viewport instead of being clipped.

A probe fetches `/?filemill=render` with `cache: "no-store"`, past the worker,
and takes the shell's mutation token, because a restarted server has a new
one. The page probes every 5 s while offline, every 30 s otherwise, when it
becomes visible, and on the browser's `online` and `offline` events. When the
server answers again after reads were answered offline, the server root is
mounted again from the URL, so every node from those reads is replaced. With no
reads offline, nothing is remounted, and an open editor keeps its draft.

A node read from a copy is `stale`, which `ui/core/ports.js` documents. The
editor treats a stale file as not editable, so an older copy cannot be saved
over newer bytes. Saves and deletes still go to the server and fail visibly
while it is offline; there are no offline writes and no edit queue.

## Rejected alternatives

- Network-only reads. Recovery would show nothing that was read before,
  against the user's decision.
- Cache-first or stale-while-revalidate reads. An online read could show an
  older copy without saying so.
- A page reload on recovery. It would discard an unsaved draft.
- One shell copy for every address. A raw file URL would open the app, and
  each shell's view and layout attributes would be lost.

## Consequences

Browsing that worked before an outage keeps working, read-only, while the
server is away, and the indicator says so. Offline copies of files stay in the
browser's Cache Storage until they are replaced or evicted, including after the
file is deleted; [SECURITY.md](../../SECURITY.md) says how to clear them. A
first visit has no worker yet, so it has no copies. A destination that was
never read gets the recovery page or a "Not available offline" column note.
Native fullscreen shows only the preview, so the top-bar indicator is not
visible there. Search, embedded images and other requests that do not use
`serverFetch` do not change the indicator.

The static edition's worker (`static/sw.js`) is unchanged and keeps its A5
defects.

## Validation

Browser tests in `server/tests/test_browser_new_ui.py` stop and restart a
server on one port under an installed worker. They first failed on `main`: no
indicator, `Failed to fetch` for offline API reads, an online read returning
the older `hello`, and activation deleting another app's cache. They cover the
indicator by click, keyboard and touch on a phone viewport, untruncated
details, warm startup from copies, uncached destinations, fresh online reads,
cache preservation on activation, failed saves and deletes, a refused change
after an unseen restart, the reconnecting state, and recovery with refreshed
content and a fresh token.
