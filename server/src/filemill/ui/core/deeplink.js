import { locationState, walkPath } from "./model/deeplink.js";
/* ═══════════════════════════════════════════════════════════════════════════
   Deep links — turning the selection into a path and back.

   Shared verbatim between the static build and the server build; only the
   ROUTER differs (a hash in one, a real URL path in the other). Everything
   here speaks in *names below the root*:

       path = [workspace, src, core]      →   ["src", "core", "state.js"]
       sel  = ["src", "core", "state.js"]

   The last segment is the selection in the deepest open column, which is the
   thing the address bar should name — a file when a file is selected, and the
   directory itself when one is open with nothing chosen inside it.
   ═══════════════════════════════════════════════════════════════════════════ */
import { revealRow } from "./layout.js";
import { FS, ROUTER } from "./ports.js";
import { path, rowIndex, sel, state } from "./model/state.js";

/* render() runs on resize and on every keystroke, so writing the URL from it is
   only safe if an unchanged location is left alone — otherwise Back fills up
   with duplicates. applying is the re-entrancy guard: a URL being *read* must
   not be immediately re-written from the half-built state it produces. */
let applying = false;
/* Named apart from render.js's exports: static/build-index.py concatenates
   every module into one script, so a module-scope `colCache` here would
   collide with the real one and the bundle would not parse. */
let renderPage, columnCache;
export const setDeepLinkActions = (
  actions,
) => ({ render: renderPage, colCache: columnCache } = actions);

let lastKey = null;

export function syncURL() {
  if (applying || !ROUTER || !path.length) return;
  const result = locationState(
    document.documentElement.dataset.filemill,
    lastKey,
  );
  ROUTER.write(result.location, result.replace);
  lastKey = result.key;
}

/* Walk down from the root, opening each directory in turn. Stops at the first
   segment that is not there — a link into a folder that has since been renamed
   still gets you as far as it can rather than showing nothing. Returns whether
   every segment was found, which is how a caller learns the chain was cut.

   `wantFocus` is for the callers that already know where the user was looking:
   a refresh must not move focus to the deepest column just because it re-walked
   the chain to get there. A link has no such opinion and omits it. */
export async function applyPath(names, wantFocus) {
  if (!path.length) return false;
  applying = true;
  try {
    const walking = walkPath(names, (node) => FS.ensureLoaded(node), wantFocus);
    const button = document.getElementById("s-dot");
    if (button) button.setAttribute("aria-checked", String(state.dotfiles));
    return await walking;
  } finally {
    applying = false;
    renderPage();
    scrollCursorIntoView();
  }
}

/* A restored selection can be thousands of rows down a column; the row exists
   but nothing has ever scrolled to it. */
export function scrollCursorIntoView() {
  for (let i = 0; i < path.length; i++) {
    const c = columnCache.get(path[i]);
    const ri = rowIndex(path[i], sel[i]);
    if (c && ri >= 0) revealRow(c.ensureRow(ri));
  }
}

/* Wire Back/Forward once a root is mounted — and only once, however many roots
   are opened after it, or one Back would replay through every listener. */
let routing = false;

export function startRouting() {
  if (routing || !ROUTER) return;
  routing = true;
  ROUTER.onNavigate((loc) => {
    /* Only the path is honoured: a Back that lands on a different root cannot
       remount it without a user gesture, so it would silently walk the wrong
       tree. Leaving the columns where they are is the honest outcome. */
    if (loc && (!loc.root || loc.root === path[0]?.name)) {
      document.documentElement.dataset.filemill = loc.view || "render";
      applyPath(loc.path);
    }
  });
}
