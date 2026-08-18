/* ═══════════════════════════════════════════════════════════════════════════
   Router — the real URL path, for the server build.

       /src/filemill/app.py

   The path *is* the file path relative to the browsed root: no mount prefix,
   no ?path=, nothing in the address bar that is not the file you are looking
   at. Query parameters stay free for representation and layout state
   (filemill-view, layout, hidden) and are preserved verbatim through every
   navigation, because they say how to show the file, not which one.

   Needs a server that serves the app shell for any path under BASE — which is
   the same requirement as any history-API single-page app.
   ═══════════════════════════════════════════════════════════════════════════ */
const BASE = (document.currentScript?.dataset.base || "/").replace(/\/*$/, "/");

const RouterPath = {
  base: BASE,

  read() {
    if (!location.pathname.startsWith(BASE)) return null;
    return {
      root: null,        /* the server decides the root; a URL cannot pick one */
      path: location.pathname.slice(BASE.length).split("/")
              .filter(Boolean).map(decodeURIComponent),
    };
  },

  write({ path }, replace) {
    const url = BASE + path.map(encodeURIComponent).join("/")
              + location.search + location.hash;
    if (url === location.pathname + location.search + location.hash) return;
    history[replace ? "replaceState" : "pushState"](null, "", url);
  },

  onNavigate(cb) {
    addEventListener("popstate", () => cb(RouterPath.read()));
  },
};
