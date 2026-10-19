/* ═══════════════════════════════════════════════════════════════════════════
   Router — the real URL path, for the server build.

       server/src/filemill/app.py

   The path *is* the file path relative to the browsed root, after BASE ("/",
   or "/n/"): no ?path=, nothing in the address bar that is not the file you
   are looking at. Query parameters stay free for representation and layout
   state, because they say how to show the file, not which one. write() sets
   `filemill` from the router state's view; every other parameter, such as
   `layout`, is preserved verbatim through every navigation.

   Needs a server that serves the app shell for any path under BASE — which is
   the same requirement as any history-API single-page app.
   ═══════════════════════════════════════════════════════════════════════════ */
import { path } from "../core/model/state.js";

const BASE = (document.documentElement.dataset.base || "/").replace(
  /\/*$/,
  "/",
);

export const RouterPath = {
  base: BASE,

  read() {
    if (!location.pathname.startsWith(BASE)) return null;
    return {
      fragment: location.hash.slice(1),
      root: null, /* the server decides the root; a URL cannot pick one */
      path: location.pathname.slice(BASE.length).split("/")
        .filter(Boolean).map(decodeURIComponent),
      view: new URLSearchParams(location.search).get("filemill") || null,
    };
  },

  write({ path, view }, replace) {
    const search = new URLSearchParams(location.search);
    if (view) search.set("filemill", view);
    else search.delete("filemill");
    const query = search.toString();
    const url = BASE + path.map(encodeURIComponent).join("/") +
      (query ? `?${query}` : "") + location.hash;
    if (url === location.pathname + location.search + location.hash) return;
    history[replace ? "replaceState" : "pushState"](null, "", url);
  },

  onNavigate(cb) {
    addEventListener("popstate", () => cb(RouterPath.read()));
  },
};
