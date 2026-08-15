# Milestone 09 – Progressive Web App

pykofinder can be installed as a standalone app on any device that supports
PWAs. This milestone supplies the three static assets that make it work:
a **Web App Manifest** declaring the app's name, theme colour, and icons;
a **service worker** with a stale-while-revalidate caching strategy for the
app shell; and an **SVG icon** that scales to any resolution.

The routes that serve these assets (`/manifest.json`, `/sw.js`,
`/icons/{name}`) were already defined in Milestone 6 – they just returned
404 because the `static/` directory didn't exist. Now they'll find their
files.

## Web App Manifest

The manifest tells the browser how to present pykofinder when installed.
`display: standalone` hides the browser chrome; `start_url: /f/` opens
the finder root; the theme colour matches the selection-highlight blue
used throughout the CSS.

```json src/pykofinder/static/manifest.json
{
  "name": "pykofinder",
  "short_name": "pykofinder",
  "description": "Finder-style column-view file browser",
  "start_url": "/f/",
  "scope": "/",
  "display": "standalone",
  "background_color": "#f0f0f0",
  "theme_color": "#0770C9",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon.svg",
      "sizes": "any",
      "type": "image/svg+xml",
      "purpose": "any"
    }
  ]
}
```

## Service worker

The service worker uses three strategies depending on the request path:

- **App shell and icons** – stale-while-revalidate: serve from cache
  immediately, update in the background.
- **Dynamic HTMX partials** (`/click`, `/restore`, `/raw`, etc.) –
  network-only, never cached.
- **Everything else** – network-first with shell fallback.

The `install` event pre-caches the shell and icon assets. The `activate`
event purges old caches when the version string changes.

```js src/pykofinder/static/sw.js
/* pykofinder service worker
 *
 * Strategy:
 *   - App shell (/f/) and static assets (icons, manifest) → cache-first,
 *     updated in background (stale-while-revalidate).
 *   - Dynamic HTMX partials (/click, /restore, /raw, /vpage, /sse/*)
 *     → network-only; never cached.
 *   - Everything else → network-first with shell fallback.
 */

const CACHE = "pykofinder-v1";

const PRECACHE = [
  "/f/",
  "/manifest.json",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/icons/icon.svg",
];

/* Paths whose responses must never be served from cache. */
const NETWORK_ONLY_PREFIXES = [
  "/click",
  "/restore",
  "/raw",
  "/vpage",
  "/sse/",
  "/open-link",
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
  const url = new URL(event.request.url);

  /* Only handle same-origin requests. */
  if (url.origin !== location.origin) return;

  const path = url.pathname;

  /* Dynamic endpoints – always hit the network. */
  if (NETWORK_ONLY_PREFIXES.some((p) => path.startsWith(p))) {
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
```

## App icon

The SVG icon depicts three column panels – a visual shorthand for the
Finder-style column view. It scales to any resolution, making it ideal
as the primary icon source.

```xml src/pykofinder/static/icons/icon.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">
  <rect width="192" height="192" fill="#0770C9"/>
  <!-- three column panels -->
  <rect x="16" y="16" width="46" height="160" rx="4" fill="#1a88e0"/>
  <rect x="73" y="16" width="46" height="160" rx="4" fill="#1a88e0"/>
  <rect x="130" y="16" width="46" height="160" rx="4" fill="#1a88e0"/>
  <!-- column header bars -->
  <rect x="16" y="16" width="46" height="36" rx="4" fill="white" opacity="0.9"/>
  <rect x="73" y="16" width="46" height="36" rx="4" fill="white" opacity="0.9"/>
  <rect x="130" y="16" width="46" height="36" rx="4" fill="white" opacity="0.9"/>
  <!-- list rows in columns -->
  <rect x="20" y="62" width="38" height="8" rx="2" fill="white" opacity="0.55"/>
  <rect x="20" y="76" width="38" height="8" rx="2" fill="white" opacity="0.55"/>
  <rect x="20" y="90" width="38" height="8" rx="2" fill="white" opacity="0.55"/>
  <rect x="20" y="104" width="28" height="8" rx="2" fill="white" opacity="0.55"/>
  <rect x="77" y="62" width="38" height="8" rx="2" fill="white" opacity="0.55"/>
  <rect x="77" y="76" width="38" height="8" rx="2" fill="white" opacity="0.55"/>
  <rect x="77" y="90" width="26" height="8" rx="2" fill="white" opacity="0.55"/>
  <rect x="134" y="62" width="38" height="8" rx="2" fill="white" opacity="0.55"/>
  <rect x="134" y="76" width="38" height="8" rx="2" fill="white" opacity="0.55"/>
  <!-- selected row highlight in first column -->
  <rect x="16" y="72" width="46" height="16" rx="2" fill="#0050A0" opacity="0.5"/>
</svg>
```

## PNG icons

The manifest references PNG icons at 192×192 and 512×512 pixels. These
binary files cannot be produced by LMT directly. Generate them from the
SVG using any SVG-to-PNG tool, for example:

```bash
# Using cairosvg (pip install cairosvg):
python -c "
import cairosvg
cairosvg.svg2png(url='src/pykofinder/static/icons/icon.svg',
                 write_to='src/pykofinder/static/icons/icon-192.png',
                 output_width=192, output_height=192)
cairosvg.svg2png(url='src/pykofinder/static/icons/icon.svg',
                 write_to='src/pykofinder/static/icons/icon-512.png',
                 output_width=512, output_height=512)
"
```

The PWA will function with just the SVG icon; the PNGs provide fallback
for platforms that don't support SVG icons.

## Verification

```bash
rm -rf _tangle_out && mkdir _tangle_out && cd _tangle_out
lmt ../01-*.md ../02-*.md ../03-*.md ../04-*.md ../05-*.md ../06-*.md ../07-*.md ../08-*.md ../09-*.md
uv sync
python -c "
from pathlib import Path
static = Path('src/pykofinder/static')
for f in sorted(static.rglob('*')):
    if f.is_file():
        print(f'  {f.relative_to(static)}  ({f.stat().st_size} bytes)')
"
```
