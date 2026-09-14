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

/* render() runs on resize and on every keystroke, so writing the URL from it is
   only safe if an unchanged location is left alone — otherwise Back fills up
   with duplicates. applying is the re-entrancy guard: a URL being *read* must
   not be immediately re-written from the half-built state it produces. */
let applying = false;

function currentPath() {
  const names = path.slice(1).map((p) => p.name);
  const leaf = sel[path.length - 1];
  if (leaf !== undefined) names.push(leaf);
  return names;
}

/* Walking a column with ↑/↓ is one selection change per keystroke — pushing a
   history entry for each would make Back useless. What counts as a navigation
   is *entering* a column, not opening one: selecting a folder opens its column
   without moving focus (that is the whole focus model), and ↑/↓ down a list of
   folders would otherwise push an entry per row. So the history key is the
   chain up to the focused column, and everything else rewrites in place.
   Back then steps back out of folders, which is what it looks like it does. */
let lastKey = null;

function syncURL() {
  if (applying || !ROUTER || !path.length) return;
  const key = path.slice(0, focusCol + 1).map((p) => p.name).join("/");
  const names = currentPath();
  const node = previewNode();
  const view = node && !node.dir
    ? document.documentElement.dataset.filemill === "highlight"
      ? "highlight"
      : "render"
    : undefined;
  ROUTER.write({ root: path[0].name, path: names, view }, lastKey === key);
  lastKey = key;
}

/* Walk down from the root, opening each directory in turn. Stops at the first
   segment that is not there — a link into a folder that has since been renamed
   still gets you as far as it can rather than showing nothing. Returns whether
   every segment was found, which is how a caller learns the chain was cut.

   `wantFocus` is for the callers that already know where the user was looking:
   a refresh must not move focus to the deepest column just because it re-walked
   the chain to get there. A link has no such opinion and omits it. */
async function applyPath(names, wantFocus) {
  if (!path.length) return false;
  names = (names || []).filter(Boolean);

  /* a link to a dotfile has to reveal dotfiles, or visibleKids would hide the
     very thing the URL asked for */
  if (!state.dotfiles && names.some((n) => n.startsWith("."))) {
    state.dotfiles = true;
    const b = document.getElementById("s-dot");
    if (b) b.setAttribute("aria-checked", "true");
  }

  applying = true;
  try {
    const rootNode = path[0];
    path = [rootNode];
    sel = [];
    cursor = { 0: 0 };
    focusCol = 0;
    await FS.ensureLoaded(rootNode);
    let complete = true;

    for (let i = 0; i < names.length; i++) {
      const parent = path[i];
      const kids = visibleKids(parent);
      const ri = kids.findIndex((k) => k.name === names[i]);
      if (ri < 0) {
        complete = false;
        break;
      }

      const node = kids[ri];
      sel[i] = node.name;
      cursor[i] = ri;
      focusCol = i; /* focus stays on the column holding it */
      parent.lastSel = node.name;
      if (!node.dir) break;
      await FS.ensureLoaded(node);
      path.push(node);
    }
    return complete;
  } finally {
    applying = false;
    /* clamped: the chain may have come back shorter than the column that had
       focus, and focusing a column that is no longer open kills ↑/↓ */
    if (wantFocus != null) {
      focusCol = Math.max(0, Math.min(wantFocus, path.length - 1));
    }
    render();
    scrollCursorIntoView();
  }
}

/* A restored selection can be thousands of rows down a column; the row exists
   but nothing has ever scrolled to it. */
function scrollCursorIntoView() {
  for (let i = 0; i < path.length; i++) {
    const c = colCache.get(path[i]);
    const ri = cursor[i];
    if (c && ri != null && c.rows[ri]) revealRow(c.rows[ri]);
  }
}

/* Wire Back/Forward once a root is mounted — and only once, however many roots
   are opened after it, or one Back would replay through every listener. */
let routing = false;

function startRouting() {
  if (routing || !ROUTER) return;
  routing = true;
  ROUTER.onNavigate((loc) => {
    /* Only the path is honoured: a Back that lands on a different root cannot
       remount it without a user gesture, so it would silently walk the wrong
       tree. Leaving the columns where they are is the honest outcome. */
    if (loc && (!loc.root || loc.root === path[0]?.name)) applyPath(loc.path);
  });
}
