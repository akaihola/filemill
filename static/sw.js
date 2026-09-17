/* filemill service worker
 *
 * Strategy:
 *   - App shell (/) and static assets (icons, manifest) → cache-first,
 *     updated in background (stale-while-revalidate).
 *   - Dynamic API responses → network-only; never cached.
 *   - Everything else → network-first with shell fallback.
 */

const CACHE = "filemill-v1";

const PRECACHE = [
  "./",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./icon.svg",
];

/* Paths whose responses must never be served from cache. */
const NETWORK_ONLY_PREFIXES = [
  "/api/",
  "/sse/",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  /* Cache Storage only supports GET requests. */
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);

  /* Only handle same-origin requests. */
  if (url.origin !== location.origin) return;

  const path = url.pathname;

  /* Dynamic endpoints – always hit the network. */
  if (NETWORK_ONLY_PREFIXES.some((p) => path.includes(p))) {
    return; /* browser default: network */
  }

  /* App shell + icons: stale-while-revalidate. */
  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const cached = await cache.match(event.request);
      const networkFetch = fetch(event.request)
        .then((response) => {
          if (response.ok) cache.put(event.request, response.clone());
          return response;
        })
        .catch(() => null);

      /* Return cached immediately, refresh in background. */
      return cached || networkFetch || new Response("Offline", { status: 503 });
    }),
  );
});
