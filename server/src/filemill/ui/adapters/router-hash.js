/* ═══════════════════════════════════════════════════════════════════════════
   Router — the fragment, for the static build.

       #r=workspace&p=src/core/state.js

   A hash and not a query string, because the static build has to survive being
   opened from anywhere: a `file://` page, a bare `python3 -m http.server`, a
   gist, a USB stick. A path-shaped URL needs a server that rewrites; a query
   string needs one that ignores it. A hash needs nothing.

   `r` names the *root folder*, and it has to be there because a
   FileSystemDirectoryHandle is not a path: the URL cannot name a folder the
   browser has not already granted. It is matched against the remembered roots
   in IndexedDB, so a link only re-opens a folder you have opened before — by
   design, since the alternative would be a page that can name arbitrary
   directories on your disk. Folder *names* are what is matched, so two
   different folders with the same basename resolve to the more recent one.
   ═══════════════════════════════════════════════════════════════════════════ */
const encSeg = (s) => encodeURIComponent(s).replace(/%2F/gi, "%2F");

/* A file:// page has an opaque origin and pushState throws SecurityError on it.
   That page cannot open a folder either (see showBlocked), so there is nothing
   to address — but the test suite does mount a fake tree there, and a throw on
   every render would be fatal. Fail once, then stay quiet. */
let dead = false;

const RouterHash = {
  read() {
    const h = location.hash.replace(/^#/, "");
    if (!h) return null;
    const q = new URLSearchParams(h);
    const p = q.get("p") || "";
    return {
      root: q.get("r") || null,
      path: p.split("/").filter(Boolean).map(decodeURIComponent),
    };
  },

  write({ root, path }, replace) {
    if (dead) return;
    const q = "#r=" + encSeg(root) +
      (path.length ? "&p=" + path.map(encSeg).join("/") : "");
    if (q === location.hash) return;
    /* history.*State, not an assignment to location.hash: assigning always
       pushes, and it fires hashchange, which would loop straight back in
       through onNavigate. */
    try {
      history[replace ? "replaceState" : "pushState"](null, "", q);
    } catch (err) {
      dead = true;
    }
  },

  onNavigate(cb) {
    addEventListener("hashchange", () => cb(RouterHash.read()));
  },
};
