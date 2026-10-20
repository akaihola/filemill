/* filemill service worker — the server edition (ADR 0089).
 *
 * Network first, for everything it handles: whatever the server answers is
 * what the page gets, so an online read is never an older copy. A complete
 * answer is also kept as an offline copy. Only when the server cannot be
 * reached (no answer, or a proxy in front of it saying 502, 503 or 504) does
 * the worker answer from those copies, marked X-Filemill-Offline: copy so the
 * page can say that the server is offline (ui/adapters/server-status.js).
 * With no copy it answers a valid 503 marked X-Filemill-Offline: miss: the
 * recovery page for a navigation, plain text for anything else.
 *
 * The copies, in caches named filemill-server-*-v2:
 *   shell   the app shell, per address that answered with it. An address the
 *           client writes (?filemill=render or highlight) gets the shell of
 *           another address when its own was never loaded.
 *   assets  /ui/, the manifest and the icons, one copy per path, so the
 *           shell's versioned module URLs find the newest copy.
 *   reads   listings, file bytes and previews: READS_MAX entries of at most
 *           COPY_MAX bytes each, the least recently stored dropped first.
 * Never handled: requests other than GET, other origins, /api/search, /sse/,
 * Range requests, and requests the page made with cache: "no-store".
 * Activation deletes older Filemill caches, filemill-v1 included, and keeps
 * every other cache on the origin.
 */

const VERSION = "v2";
const SHELL = `filemill-server-shell-${VERSION}`;
const ASSETS = `filemill-server-assets-${VERSION}`;
const READS = `filemill-server-reads-${VERSION}`;
const CURRENT = [SHELL, ASSETS, READS];
/* The caches this worker owns: its own, and the one every older build used. */
const ours = (name) =>
  name === "filemill-v1" || name.startsWith("filemill-server-");

const SHELL_MAX = 50;
const READS_MAX = 200;
const COPY_MAX = 2 * 1024 * 1024;

const OFFLINE = "X-Filemill-Offline";
/* What a proxy answers when the Filemill server behind it does not. */
const UNAVAILABLE = [502, 503, 504];

/* Paths whose responses must never be served from cache. */
const NETWORK_ONLY_PREFIXES = [
  "/api/search",
  "/sse/",
];
const ASSET_PREFIXES = ["/ui/", "/icons/", "/manifest.json"];

const RECOVERY_HTML = `<!doctype html>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Filemill server unavailable</title>
<style>body{font:16px system-ui,sans-serif;max-width:36rem;margin:20vh auto;padding:1rem;color:#222}button{font:inherit;padding:.6rem 1rem}</style>
<h1>Filemill server unavailable</h1>
<p>Filemill cannot reach its server, and this address has no copy saved for offline use.</p>
<p>Start Filemill on the machine that serves it, for example with <code>uv run filemill [ROOT]</code>, then retry. The installed app can connect to the server but cannot start it.</p>
<button onclick="location.reload()">Retry connection</button>`;

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) =>
        Promise.all(
          names
            .filter((name) => ours(name) && !CURRENT.includes(name))
            .map((name) => caches.delete(name)),
        )
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  /* Cache Storage only supports GET requests. */
  if (event.request.method !== "GET") return;

  const url = new URL(request.url);

  /* Only handle same-origin requests. */
  if (url.origin !== location.origin) return;

  /* Dynamic endpoints, partial reads and probes – always the network. */
  if (
    NETWORK_ONLY_PREFIXES.some((p) => url.pathname.startsWith(p)) ||
    request.headers.has("Range") || request.cache === "no-store"
  ) {
    return; /* browser default: network */
  }

  if (event.request.mode === "navigate") {
    event.respondWith(navigate(event, url));
    return;
  }

  event.respondWith(
    ASSET_PREFIXES.some((p) => url.pathname.startsWith(p))
      ? read(event, ASSETS, url.origin + url.pathname, Infinity)
      : read(event, READS, request.url, READS_MAX),
  );
});

/* The server's answer, or undefined when the server could not give one. */
async function network(request) {
  try {
    const response = await fetch(request);
    return UNAVAILABLE.includes(response.status) ? undefined : response;
  } catch {
    return undefined;
  }
}

async function navigate(event, url) {
  const response = await network(event.request);
  if (response) {
    if (response.headers.has("X-Filemill-Shell") && keepable(response)) {
      event.waitUntil(keep(SHELL, url.href, response.clone(), SHELL_MAX));
    }
    return response;
  }
  const copy = await shellFor(url);
  return copy
    ? marked(copy, "copy")
    : missing(RECOVERY_HTML, "text/html; charset=utf-8");
}

/* The shell differs between addresses only by the view, layout and hidden
   switches in the query, so a view address can borrow another one's. A bare
   address may name file bytes or a user's index.html; it gets only its own. */
async function shellFor(url) {
  const cache = await caches.open(SHELL);
  const own = await cache.match(url.href);
  if (own) return own;
  if (!["render", "highlight"].includes(url.searchParams.get("filemill"))) {
    return undefined;
  }
  const keys = await cache.keys();
  const key = keys.findLast((k) => new URL(k.url).search === url.search) ||
    keys.at(-1);
  return key && cache.match(key);
}

async function read(event, name, key, max) {
  const response = await network(event.request);
  if (response) {
    if (keepable(response)) {
      event.waitUntil(keep(name, key, response.clone(), max));
    }
    return response;
  }
  const copy = await (await caches.open(name)).match(key);
  return copy
    ? marked(copy, "copy")
    : missing("Filemill server unavailable", "text/plain; charset=utf-8");
}

const keepable = (response) =>
  response.status === 200 && response.type === "basic" &&
  Number(response.headers.get("Content-Length") ?? Infinity) <= COPY_MAX;

/* Store a copy as the newest entry; past `max` entries, drop the oldest. */
async function keep(name, key, response, max) {
  const cache = await caches.open(name);
  await cache.delete(key);
  await cache.put(key, response);
  const keys = await cache.keys();
  if (keys.length > max) {
    await Promise.all(
      keys.slice(0, keys.length - max).map((k) => cache.delete(k)),
    );
  }
}

function marked(response, kind) {
  const headers = new Headers(response.headers);
  headers.set(OFFLINE, kind);
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

const missing = (body, type) =>
  new Response(body, {
    status: 503,
    headers: { "Content-Type": type, [OFFLINE]: "miss" },
  });
