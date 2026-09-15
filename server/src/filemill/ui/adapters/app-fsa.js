/* ═══════════════════════════════════════════════════════════════════════════
   Static build — boot, folder picker, welcome screen.

   The only file that knows this is the local-folder flavour of the app. It
   picks the adapters (fsa + preview-rich + router-hash, imported below) and
   owns the one entry point into the tree, mount(). ../entry-static.js is what
   the page loads; this is the module it ends with.
   ═══════════════════════════════════════════════════════════════════════════ */
import { initSettings } from "../core/settings.js";
import { initLayout } from "../core/layout.js";
import { initSort, setSortActions, sortKids } from "../core/sort.js";
import { FSA } from "./fsa.js";
import { PreviewRich } from "./preview-rich.js";
import { RouterHash } from "./router-hash.js";
import { recallRoots, recallView, rememberRoot } from "./storage.js";
import { withCsv, withCsvPreview } from "./vfs-csv.js";
import {
  applyPath,
  setDeepLinkActions,
  startRouting,
} from "../core/deeplink.js";
import { FOLDER_PATH } from "../core/icons.js";
import { mountRoot } from "../core/mount.js";
import {
  withJson,
  withJsonl,
  withJsonlPreview,
  withJsonPreview,
} from "../core/jsonl.js";
import {
  FS,
  ROUTER,
  useFilesystem,
  usePreview,
  useRouter,
} from "../core/ports.js";
import { colCache, render, setActions } from "../core/render.js";
import {
  choose,
  refreshColumn,
  renderCrumbs,
  saySt,
  unfoldTo,
} from "../core/nav.js";
import {
  focusCol,
  path,
  root,
  sel,
  setSortKids,
  setState,
  welcome,
} from "../core/state.js";

/* The load-time work sort.js, layout.js and settings.js did as classic scripts,
   in the order they used to load. */
initSort();
setSortKids(sortKids);
setActions({ choose, refreshColumn, renderCrumbs, saySt, unfoldTo });
setSortActions({ render });
setDeepLinkActions({ render, colCache });
initLayout(render);
initSettings();

/* Adapters define themselves; the app entry is what chooses. Selecting here
   rather than at the bottom of each adapter file means a page may load more
   than one of them — which the server build does — without import order
   silently deciding which wins. */
useFilesystem(withCsv(withJson(withJsonl(FSA))));
usePreview(withCsvPreview(withJsonPreview(withJsonlPreview(PreviewRich))));
/* The router is already the one place that hears "the selection changed": core
   writes the location there and nowhere else. Wrapping write() here, rather
   than adding a hook to core, keeps remembering in the only file that knows
   this build has remembered folders at all — the server build has none. */
useRouter({
  ...RouterHash,
  write(loc, replace) {
    RouterHash.write(loc, replace);
    keepView(loc);
  },
});

/* A deep link read at startup, held until a root is mounted that can satisfy
   it — the URL names a folder, but a folder is not browsable until the browser
   has granted it. */
export let pendingLoc = null;
export const setPendingLoc = (loc) => pendingLoc = loc;

/* ── Where the user was, per folder ─────────────────────────────────────────
   Saved against the mounted root and restored on the way back in. `mounted` is
   set only once a root is fully mounted: a save fired mid-mount would store the
   bare root and overwrite the very chain the mount is about to restore. */
let mounted = null, pendingView = null, viewTimer = null, keptAt = null;

/* Debounced, because walking a column with ↓ held is one location change per
   keystroke, and an IndexedDB write per keystroke is the O(entries) mistake in
   a different costume. Unchanged locations return before touching the timer:
   render() also runs on resize and on the font load, and rescheduling on those
   would let a busy page starve the write it is waiting to make. */
function keepView(loc) {
  if (!mounted || !loc) return;
  const at = loc.path.join("/");
  if (at === keptAt) return;
  keptAt = at;
  pendingView = { handle: mounted, path: loc.path };
  clearTimeout(viewTimer);
  viewTimer = setTimeout(flushView, 400);
}

/* Also flushed on the way out. A tab closed 100 ms after the last click would
   otherwise lose that click, and "it forgot the last thing I did" is the
   failure people actually notice. */
function flushView() {
  clearTimeout(viewTimer);
  const p = pendingView;
  pendingView = null;
  if (p) rememberRoot(p.handle, p.path);
}
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") flushView();
});

export async function mount(handle, loc) {
  const node = FS.node(handle.name, handle);
  mounted = null;
  keptAt = null;
  welcome.hidden = true;
  await mountRoot(node, handle.name + " — Filemill");
  /* A link in the address bar beats the remembered chain: the user followed it
     just now, where the chain is only where they happened to stop last time.
     applyPath walks as far as the names still exist and stops, so a folder
     deleted since the last visit lands them at the deepest part that is real
     rather than on a selection that is not. */
  const want = loc ?? takePending(handle.name) ?? await recallView(handle);
  if (want && want.path.length) await applyPath(want.path);
  else render();
  mounted = handle;
  startRouting();
}

/* A pending link only applies to the root it named — mounting some other folder
   must not try to walk that folder's path into it. */
function takePending(rootName) {
  const p = pendingLoc;
  pendingLoc = null;
  return p && (!p.root || p.root === rootName) ? p : null;
}

async function pickFolder() {
  if (!window.showDirectoryPicker) return showBlocked("unsupported");
  try {
    const handle = await window.showDirectoryPicker({
      mode: "read",
      id: "filemill",
    });
    await rememberRoot(handle);
    await mount(handle);
  } catch (err) {
    if (err.name === "AbortError") return;
    /* Chrome refuses the picker on an opaque origin — i.e. a file:// page */
    if (err.name === "SecurityError") return showBlocked("file");
    console.error(err);
  }
}

/* Opening a remembered folder. 'granted' mounts straight away; anything else
   needs requestPermission(), which is only allowed from this click. */
async function openRemembered(root) {
  const perm = await root.handle.queryPermission({ mode: "read" });
  if (
    perm === "granted" ||
    await root.handle.requestPermission({ mode: "read" }) === "granted"
  ) {
    return mount(root.handle);
  }
}

function renderRecents(roots) {
  const box = document.getElementById("w-recent");
  const list = box.querySelector(".rec-list");
  list.textContent = "";
  roots.forEach((r) => {
    const b = document.createElement("button");
    b.className = "rec";
    b.innerHTML =
      `<svg viewBox="0 0 16 16" aria-hidden="true">${FOLDER_PATH}</svg>`;
    b.appendChild(document.createTextNode(r.handle.name));
    /* Say where the click will land. The chain is the point of the button, and
       a folder that reopens three columns deep is a surprise worth spending
       one line of the welcome screen on. */
    if (r.path.length) {
      const where = document.createElement("span");
      where.className = "rec-where";
      where.textContent = "› " + r.path.join(" › ");
      b.appendChild(where);
    }
    b.onclick = () => openRemembered(r);
    list.appendChild(b);
  });
  box.hidden = !roots.length;
}

/* Both failure modes end at the welcome screen, since there is nothing to show
   without a folder. Keep the wording actionable — the fix differs per case. */
function showBlocked(why) {
  welcome.hidden = false;
  document.getElementById("w-pick").hidden = why === "unsupported";
  document.getElementById("w-recent").hidden = true;
  document.getElementById("w-msg").innerHTML = why === "unsupported"
    ? "This browser has no File System Access API, so local folders cannot be opened. " +
      "Try Chrome, Edge or another Chromium-based desktop browser."
    : "Chrome blocks folder access on <code>file://</code> pages. Serve this file over " +
      "localhost instead:<br><code>python3 -m http.server -d " +
      "&lt;folder containing index.html&gt;</code><br>then open " +
      "<code>http://localhost:8000/index.html</code>.";
}

document.getElementById("open").onclick = pickFolder;
document.getElementById("w-pick").onclick = pickFolder;

(async function start() {
  if (!window.showDirectoryPicker) return showBlocked("unsupported");
  if (location.protocol === "file:") return showBlocked("file");

  pendingLoc = ROUTER.read();
  const roots = await recallRoots();
  if (!roots.length) return;

  /* A link names its root, so prefer that folder over the most recent one —
     otherwise reopening a bookmark would silently browse the wrong tree. */
  const wanted = pendingLoc?.root
    ? roots.find((r) => r.handle.name === pendingLoc.root)
    : null;
  const first = wanted || roots[0];

  /* queryPermission needs no gesture, so a folder still granted from an earlier
     visit opens with no dialog at all — and mount() puts the user back on the
     chain it stored, so the whole return trip costs no clicks */
  if (await first.handle.queryPermission({ mode: "read" }) === "granted") {
    return mount(first.handle);
  }
  renderRecents(roots);
})();

document.fonts.ready.then(() => render(true));
